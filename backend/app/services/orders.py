from app.core.errors import APIError
from app.repositories.orders import OrderRepository
from app.schemas.checkout import OrderDetailData
from app.schemas.orders import OrderList, OrderQuery
from app.services.access import AccessPolicy


class OrderService:
    def __init__(self, access: AccessPolicy):
        buyer = access.buyer()
        self.repository = OrderRepository(access.repository.session, buyer.user_id)

    def list(self, query: OrderQuery) -> OrderList:
        return self.repository.list(query)

    def detail(self, order_id: int) -> OrderDetailData:
        order = self.repository.owned(order_id)
        if order is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy đơn hàng")
        return self.repository.detail(order)
