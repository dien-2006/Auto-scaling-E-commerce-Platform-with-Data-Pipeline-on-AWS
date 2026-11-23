"""Offline regression checks; no credentials, AWS access, Glue or Spark runtime needed."""
import ast
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import re
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import boto3
from botocore.stub import Stubber

# Never load the developer's real .env while importing application modules.
with patch('dotenv.load_dotenv', return_value=False):
    import check_aws
    from common.aws_clients import AWSClients
    from extract import setup_workflow, run_workflow

ROOT = Path(__file__).resolve().parents[2]
EXTRACT_JOB = 'ecommerce-dev-extract'
TRANSFORM_JOB = 'ecommerce-dev-transform'


def literal_assignment(path, name):
    tree = ast.parse((ROOT / path).read_text())
    return next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in node.targets))


def glue_client():
    # Explicit dummy credentials prevent credential discovery and IMDS access.
    return boto3.client('glue', region_name='ap-southeast-1',
                        aws_access_key_id='testing', aws_secret_access_key='testing')


def completed_run():
    return {
        'Status': 'COMPLETED',
        'Statistics': {'TotalActions': 2, 'SucceededActions': 2,
                       'FailedActions': 0, 'TimeoutActions': 0,
                       'StoppedActions': 0, 'ErroredActions': 0},
        'Graph': {'Nodes': [
            {'Type': 'JOB', 'Name': job,
             'JobDetails': {'JobRuns': [{'Id': 'jr_' + job, 'JobRunState': 'SUCCEEDED'}]}}
            for job in [EXTRACT_JOB, TRANSFORM_JOB]
        ]},
    }


class QuietTest(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.enterContext(redirect_stdout(self.output))
        self.enterContext(redirect_stderr(self.output))


class SchemaContractTests(unittest.TestCase):
    def test_extract_columns_and_transform_keys_exist_in_sql(self):
        sql = (ROOT / 'sql/marketplace_schema.sql').read_text()
        blocks = {m.group(1): m.group(2) for m in re.finditer(
            r'CREATE TABLE marketplace\.(\w+)\s*\((.*?)\n\);', sql, re.S)}
        tables = literal_assignment('etl/extract/extract_postgres.py', 'TABLES')
        keys = literal_assignment('etl/transform/transform.py', 'PRIMARY_KEYS')
        self.assertEqual(set(tables), set(keys))
        for table, columns in tables.items():
            with self.subTest(table=table):
                self.assertIn(table, blocks)
                actual = set(re.findall(
                    r'^\s*(\w+)\s+(?:BIGINT|INTEGER|VARCHAR|NUMERIC|BOOLEAN|TIMESTAMPTZ|TEXT|UUID)',
                    blocks[table], re.M))
                self.assertTrue(set(columns) <= actual, set(columns) - actual)
                self.assertIn(keys[table], columns)
        # All inputs used by the three Gold builders must still be available.
        self.assertTrue({'shops', 'categories', 'products', 'inventory',
                         'orders', 'shop_orders', 'order_items'} <= set(tables))


class AWSCheckTests(QuietTest):
    def settings(self):
        return SimpleNamespace(
            environment='dev', region='ap-southeast-1', profile=None,
            account_id='123456789012', bucket='example-etl-bucket',
            extract_job=EXTRACT_JOB, transform_job=TRANSFORM_JOB,
            athena_workgroup='ecommerce-dev-analytics',
            athena_database='ecommerce_dev_analytics',
        )

    def test_clients_expose_the_verified_identity(self):
        settings = self.settings()
        identity = {'Account': settings.account_id,
                    'Arn': 'arn:aws:iam::123456789012:user/test'}
        with patch('common.aws_clients.get_settings', return_value=settings), \
                patch('common.aws_clients.boto3.Session') as session:
            session.return_value.client.return_value.get_caller_identity.return_value = identity
            aws = AWSClients()
        self.assertEqual(aws.identity, identity)
        session.assert_called_once_with(region_name=settings.region)

    def test_wrong_account_is_rejected_before_other_clients(self):
        with patch('common.aws_clients.get_settings', return_value=self.settings()), \
                patch('common.aws_clients.boto3.Session') as session:
            session.return_value.client.return_value.get_caller_identity.return_value = {'Account': '999999999999'}
            with self.assertRaisesRegex(RuntimeError, 'account mismatch'):
                AWSClients()
            self.assertEqual(session.return_value.client.call_count, 1)

    def test_check_resources_uses_current_settings_and_client_api(self):
        aws = SimpleNamespace(settings=self.settings(), identity={
            'Account': '123456789012', 'Arn': 'arn:aws:iam::123456789012:user/test'})
        options = dict(region_name='ap-southeast-1', aws_access_key_id='testing',
                       aws_secret_access_key='testing')
        aws.s3 = boto3.client('s3', **options)
        aws.glue = boto3.client('glue', **options)
        aws.athena = boto3.client('athena', **options)
        with Stubber(aws.s3) as s3, Stubber(aws.glue) as glue, Stubber(aws.athena) as athena:
            s3.add_response('head_bucket', {}, {'Bucket': aws.settings.bucket})
            for job in [EXTRACT_JOB, TRANSFORM_JOB]:
                glue.add_response('get_job', {'Job': {'Name': job}}, {'JobName': job})
            athena.add_response('get_work_group', {'WorkGroup': {'Name': aws.settings.athena_workgroup}},
                                {'WorkGroup': aws.settings.athena_workgroup})
            glue.add_response('get_database', {'Database': {'Name': aws.settings.athena_database}},
                              {'Name': aws.settings.athena_database})
            with patch('check_aws.AWSClients', return_value=aws):
                self.assertEqual(check_aws.main(), 0)
            for stub in [s3, glue, athena]:
                stub.assert_no_pending_responses()

    def test_check_failure_returns_nonzero(self):
        with patch('check_aws.AWSClients', side_effect=RuntimeError('wrong account')):
            self.assertEqual(check_aws.main(), 1)


class WorkflowTests(QuietTest):
    def test_completed_both_jobs_succeeded(self):
        run_workflow.validate_success(completed_run(), [EXTRACT_JOB, TRANSFORM_JOB])

    def test_completed_with_unsuccessful_actions_is_rejected(self):
        for key in run_workflow.FAILED_ACTION_COUNTS:
            with self.subTest(key=key):
                run = completed_run()
                run['Statistics'][key] = 1
                with self.assertRaisesRegex(RuntimeError, 'unsuccessful actions'):
                    run_workflow.validate_success(run, [EXTRACT_JOB, TRANSFORM_JOB])

    def test_completed_without_transform_is_rejected(self):
        run = completed_run()
        run['Graph']['Nodes'].pop()
        with self.assertRaisesRegex(RuntimeError, TRANSFORM_JOB):
            run_workflow.validate_success(run, [EXTRACT_JOB, TRANSFORM_JOB])

    def test_completed_with_failed_job_graph_is_rejected(self):
        run = completed_run()
        run['Graph']['Nodes'][1]['JobDetails']['JobRuns'][0]['JobRunState'] = 'FAILED'
        with self.assertRaisesRegex(RuntimeError, TRANSFORM_JOB):
            run_workflow.validate_success(run, [EXTRACT_JOB, TRANSFORM_JOB])

    def test_incomplete_statistics_are_rejected(self):
        for statistics in [{}, {'TotalActions': 2, 'SucceededActions': 1}]:
            run = completed_run()
            run['Statistics'] = statistics
            with self.assertRaises(RuntimeError):
                run_workflow.validate_success(run, [EXTRACT_JOB, TRANSFORM_JOB])

    def test_terminal_failure_is_rejected(self):
        for status in ['ERROR', 'STOPPED']:
            with self.assertRaisesRegex(RuntimeError, status):
                run_workflow.validate_success({'Status': status}, [EXTRACT_JOB, TRANSFORM_JOB])

    def test_watch_requests_graph_and_waits_for_completion(self):
        glue = glue_client()
        expected = {'Name': 'flow', 'RunId': 'run-1', 'IncludeGraph': True}
        with Stubber(glue) as stub, patch('extract.run_workflow.time.sleep'):
            stub.add_response('get_workflow_run', {'Run': {'Status': 'RUNNING'}}, expected)
            stub.add_response('get_workflow_run', {'Run': completed_run()}, expected)
            result = run_workflow.wait_for_workflow(glue, 'flow', 'run-1', [EXTRACT_JOB, TRANSFORM_JOB])
            self.assertEqual(result['Status'], 'COMPLETED')
            stub.assert_no_pending_responses()

    def test_watch_timeout_does_not_stop_aws_run(self):
        glue = glue_client()
        expected = {'Name': 'flow', 'RunId': 'run-1', 'IncludeGraph': True}
        with Stubber(glue) as stub, patch('extract.run_workflow.time.sleep'), \
                patch('extract.run_workflow.time.monotonic', side_effect=[0, 0, 2]):
            for _ in range(2):
                stub.add_response('get_workflow_run', {'Run': {'Status': 'RUNNING'}}, expected)
            with self.assertRaisesRegex(TimeoutError, 'has not been stopped'):
                run_workflow.wait_for_workflow(glue, 'flow', 'run-1',
                                              [EXTRACT_JOB, TRANSFORM_JOB], timeout_seconds=1)
            stub.assert_no_pending_responses()


class TriggerTests(QuietTest):
    def setUp(self):
        super().setUp()
        self.glue = glue_client()
        self.stub = self.enterContext(Stubber(self.glue))
        self.enterContext(patch('extract.setup_workflow.time.sleep'))

    def get_state(self, state):
        self.stub.add_response('get_trigger', {'Trigger': {
            'Name': 'trigger', 'Type': 'CONDITIONAL', 'WorkflowName': 'flow', 'State': state,
        }}, {'Name': 'trigger'})

    def test_activate_waits_through_creation_and_activation(self):
        for state in ['CREATING', 'UPDATING', 'CREATED']:
            self.get_state(state)
        self.stub.add_response('start_trigger', {'Name': 'trigger'}, {'Name': 'trigger'})
        for state in ['CREATED', 'ACTIVATING', 'ACTIVATED']:
            self.get_state(state)
        setup_workflow.ensure_active(self.glue, 'trigger')
        self.stub.assert_no_pending_responses()

    def test_disable_waits_for_inflight_activation(self):
        for state in ['ACTIVATING', 'ACTIVATED']:
            self.get_state(state)
        self.stub.add_response('stop_trigger', {'Name': 'trigger'}, {'Name': 'trigger'})
        for state in ['DEACTIVATING', 'DEACTIVATED']:
            self.get_state(state)
        setup_workflow.ensure_disabled(self.glue, 'trigger')
        self.stub.assert_no_pending_responses()

    def test_already_active_does_not_restart(self):
        self.get_state('ACTIVATED')
        setup_workflow.ensure_active(self.glue, 'trigger')
        self.stub.assert_no_pending_responses()

    def test_created_schedule_does_not_need_stopping(self):
        self.get_state('CREATED')
        setup_workflow.ensure_disabled(self.glue, 'trigger')
        self.stub.assert_no_pending_responses()

    def test_transitional_state_times_out(self):
        self.get_state('CREATING')
        self.get_state('CREATING')
        with patch('extract.setup_workflow.time.monotonic', side_effect=[0, 0, 2]):
            with self.assertRaisesRegex(TimeoutError, 'CREATING'):
                setup_workflow.wait_for_trigger(self.glue, 'trigger', timeout_seconds=1)
        self.stub.assert_no_pending_responses()

    def test_deleting_trigger_is_reported(self):
        self.get_state('DELETING')
        with self.assertRaisesRegex(RuntimeError, 'DELETING'):
            setup_workflow.ensure_active(self.glue, 'trigger')
        self.stub.assert_no_pending_responses()

    def test_creation_waits_for_trigger_to_be_visible_and_ready(self):
        self.stub.add_client_error('get_trigger', 'EntityNotFoundException', expected_params={'Name': 'trigger'})
        config = {'Actions': [{'JobName': TRANSFORM_JOB}]}
        self.stub.add_response('create_trigger', {'Name': 'trigger'}, {
            'Name': 'trigger', 'WorkflowName': 'flow', 'Type': 'CONDITIONAL',
            'StartOnCreation': False, **config,
        })
        self.stub.add_client_error('get_trigger', 'EntityNotFoundException', expected_params={'Name': 'trigger'})
        for state in ['CREATING', 'CREATED']:
            self.get_state(state)
        setup_workflow.ensure_trigger(self.glue, 'trigger', 'CONDITIONAL', config, 'flow')
        self.stub.assert_no_pending_responses()


class StartingTriggerTests(QuietTest):
    def setUp(self):
        super().setUp()
        self.glue = glue_client()
        self.stub = self.enterContext(Stubber(self.glue))
        self.enterContext(patch('extract.setup_workflow.time.sleep'))
        self.manual = 'coco-dev-manual-extract'
        self.scheduled = 'coco-dev-scheduled-extract'

    def trigger(self, name, kind, state='CREATED', workflow='flow'):
        self.stub.add_response('get_trigger', {'Trigger': {
            'Name': name, 'Type': kind, 'State': state, 'WorkflowName': workflow,
            'Actions': [{'JobName': EXTRACT_JOB}],
        }}, {'Name': name})

    def missing(self, name):
        self.stub.add_client_error('get_trigger', 'EntityNotFoundException', expected_params={'Name': name})

    def create_manual(self):
        self.missing(self.manual)
        self.stub.add_response('create_trigger', {'Name': self.manual}, {
            'Name': self.manual, 'WorkflowName': 'flow', 'Type': 'ON_DEMAND',
            'StartOnCreation': False, 'Actions': [{'JobName': EXTRACT_JOB}],
        })
        self.trigger(self.manual, 'ON_DEMAND')

    def setup_start(self, replace=False):
        return setup_workflow.ensure_start_trigger(
            self.glue, 'flow', 'coco-dev', EXTRACT_JOB, 'cron(0 1 * * ? *)', replace=replace)

    def test_fresh_workflow_creates_only_one_on_demand_start(self):
        self.missing(self.scheduled)
        self.create_manual()
        self.assertEqual(self.setup_start(), self.manual)
        self.stub.assert_no_pending_responses()

    def test_full_setup_creates_an_explicit_success_predicate_and_activates_it(self):
        settings = SimpleNamespace(environment='dev', workflow='flow', extract_job=EXTRACT_JOB,
                                   transform_job=TRANSFORM_JOB, schedule='cron(0 1 * * ? *)')
        for job in (EXTRACT_JOB, TRANSFORM_JOB):
            self.stub.add_response('get_job', {'Job': {'Name': job}}, {'JobName': job})
        self.stub.add_response('get_workflow', {'Workflow': {'Name': 'flow', 'MaxConcurrentRuns': 1}}, {'Name': 'flow'})
        self.missing(self.scheduled)
        self.create_manual()
        conditional = 'coco-dev-conditional-transform'
        predicate = {'Logical': 'AND', 'Conditions': [
            {'LogicalOperator': 'EQUALS', 'JobName': EXTRACT_JOB, 'State': 'SUCCEEDED'},
        ]}
        self.missing(conditional)
        self.stub.add_response('create_trigger', {'Name': conditional}, {
            'Name': conditional, 'WorkflowName': 'flow', 'Type': 'CONDITIONAL',
            'StartOnCreation': False, 'Predicate': predicate, 'Actions': [{'JobName': TRANSFORM_JOB}],
        })
        for state in ('CREATED', 'CREATED'):
            self.stub.add_response('get_trigger', {'Trigger': {
                'Name': conditional, 'WorkflowName': 'flow', 'Type': 'CONDITIONAL',
                'State': state, 'Predicate': predicate, 'Actions': [{'JobName': TRANSFORM_JOB}],
            }}, {'Name': conditional})
        self.stub.add_response('start_trigger', {'Name': conditional}, {'Name': conditional})
        self.stub.add_response('get_trigger', {'Trigger': {
            'Name': conditional, 'WorkflowName': 'flow', 'Type': 'CONDITIONAL',
            'State': 'ACTIVATED', 'Predicate': predicate, 'Actions': [{'JobName': TRANSFORM_JOB}],
        }}, {'Name': conditional})
        with patch('extract.setup_workflow.AWSClients', return_value=SimpleNamespace(glue=self.glue, settings=settings)), \
                patch('sys.argv', ['setup_workflow', '--disable-schedule']):
            self.assertEqual(setup_workflow.main(), 0)
        self.stub.assert_no_pending_responses()

    def test_rerun_reuses_the_manual_start_without_a_second_start(self):
        self.missing(self.scheduled)
        self.trigger(self.manual, 'ON_DEMAND')
        self.trigger(self.manual, 'ON_DEMAND')
        self.setup_start()
        self.stub.assert_no_pending_responses()

    def test_old_schedule_is_never_deleted_without_explicit_replacement(self):
        self.trigger(self.scheduled, 'SCHEDULED')
        with self.assertRaisesRegex(RuntimeError, '--replace-start-trigger'):
            self.setup_start()
        self.stub.assert_no_pending_responses()

    def test_running_workflow_blocks_trigger_replacement(self):
        self.trigger(self.scheduled, 'SCHEDULED')
        self.stub.add_response('get_workflow_runs', {'Runs': [{'Status': 'RUNNING'}]}, {'Name': 'flow'})
        with self.assertRaisesRegex(RuntimeError, 'Workflow is active'):
            self.setup_start(replace=True)
        self.stub.assert_no_pending_responses()

    def test_replacement_waits_for_old_trigger_deletion_then_creates_only_manual(self):
        self.trigger(self.scheduled, 'SCHEDULED')
        # Botocore's Runs shape requires at least one item when present.
        # A completed run is valid history and must not block replacement.
        self.stub.add_response('get_workflow_runs', {'Runs': [{'Status': 'COMPLETED'}]}, {'Name': 'flow'})
        self.trigger(self.scheduled, 'SCHEDULED')
        self.stub.add_response('get_workflow_runs', {'Runs': [{'Status': 'COMPLETED'}]}, {'Name': 'flow'})
        self.stub.add_response('delete_trigger', {'Name': self.scheduled}, {'Name': self.scheduled})
        self.trigger(self.scheduled, 'SCHEDULED', state='DELETING')
        self.missing(self.scheduled)
        self.create_manual()
        self.setup_start(replace=True)
        self.stub.assert_no_pending_responses()

    def test_trigger_from_another_workflow_cannot_be_replaced(self):
        self.trigger(self.scheduled, 'SCHEDULED', workflow='other-flow')
        with self.assertRaisesRegex(RuntimeError, 'unrelated trigger'):
            self.setup_start(replace=True)
        self.stub.assert_no_pending_responses()


if __name__ == '__main__':
    unittest.main()
