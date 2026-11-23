from sqlalchemy import select

from app.models import Category


class AdminCategoryRepository:
    def __init__(self, session):
        self.session = session

    def rows(self):
        return list(
            self.session.scalars(
                select(Category).order_by(Category.category_name, Category.category_id)
            )
        )

    def add(self, values):
        row = Category(**values)
        self.session.add(row)
        return row

    def flush(self):
        self.session.flush()
