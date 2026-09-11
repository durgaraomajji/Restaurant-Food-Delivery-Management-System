from fastapi import APIRouter,WebSocket,WebSocketDisconnect
from ..database import SessionLocal
from ..models.models import Tracking
router=APIRouter(tags=['Bonus Real-time Tracking'])
@router.websocket('/ws/orders/{order_id}')
async def order_socket(websocket:WebSocket,order_id:int):
    await websocket.accept()
    try:
        db=SessionLocal()
        while True:
            rows=db.query(Tracking).filter_by(order_id=order_id).order_by(Tracking.timestamp.desc()).limit(10).all()
            await websocket.send_json([{'status':r.status,'location':r.location,'remarks':r.remarks,'timestamp':r.timestamp.isoformat()} for r in rows])
            msg=await websocket.receive_text()
            if msg.lower() in ('close','disconnect'): break
    except WebSocketDisconnect: pass
    finally:
        try: db.close()
        except Exception: pass
