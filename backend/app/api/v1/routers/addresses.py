from typing import Annotated

from fastapi import APIRouter, Path, Response

from app.api.dependencies import ReadAccess, WriteAccess
from app.schemas.addresses import (
    AddressCreate,
    AddressItems,
    AddressList,
    AddressPatch,
    AddressResponse,
)
from app.services.addresses import AddressService

router = APIRouter(prefix="/addresses", tags=["Buyer addresses"])
AddressID = Annotated[int, Path(ge=1, le=9223372036854775807)]


@router.get("", response_model=AddressList)
def addresses(access: ReadAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return AddressList(data=AddressItems(items=AddressService(access).list()))


@router.post("", response_model=AddressResponse, status_code=201)
def create_address(payload: AddressCreate, access: WriteAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return AddressResponse(data=AddressService(access).save(payload))


@router.patch("/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: AddressID, payload: AddressPatch, access: WriteAccess, response: Response
):
    response.headers["Cache-Control"] = "no-store"
    return AddressResponse(data=AddressService(access).save(payload, address_id))


@router.delete("/{address_id}", status_code=204)
def delete_address(address_id: AddressID, access: WriteAccess):
    AddressService(access).delete(address_id)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
