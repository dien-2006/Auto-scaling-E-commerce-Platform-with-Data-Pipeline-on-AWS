from app.core.errors import APIError
from app.models import Address
from app.repositories.addresses import AddressRepository
from app.schemas.addresses import AddressCreate, AddressData, AddressPatch
from app.services.access import AccessPolicy


def public_address(row: Address) -> AddressData:
    return AddressData(
        address_id=str(row.address_id),
        **{name: getattr(row, name) for name in AddressData.model_fields if name != "address_id"},
    )


class AddressService:
    def __init__(self, access: AccessPolicy):
        self.repository = AddressRepository(access.repository.session, access.buyer().user_id)

    def list(self) -> list[AddressData]:
        return [public_address(row) for row in self.repository.list()]

    def save(
        self, payload: AddressCreate | AddressPatch, address_id: int | None = None
    ) -> AddressData:
        # WriteAccess locks the user before this service. All address writes use
        # that same transaction, serializing default changes across replicas.
        row = self.repository.get(address_id) if address_id is not None else None
        if address_id is not None and row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy địa chỉ")
        values = payload.model_dump(exclude_unset=isinstance(payload, AddressPatch))
        if values.get("is_default") is True:
            self.repository.clear_default()
        if row is None:
            row = self.repository.add(values)
        else:
            for name, value in values.items():
                setattr(row, name, value)
        self.repository.session.flush()
        return public_address(row)

    def delete(self, address_id: int) -> None:
        row = self.repository.get(address_id)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy địa chỉ")
        self.repository.session.delete(row)
        self.repository.session.flush()
        # Zero defaults is allowed. Never change historical order snapshots.
