from ..models.models import Notification

def create_notification(db,user_id,order_id,event,message):
    db.add(Notification(user_id=user_id,order_id=order_id,event=event,message=message))

def background_log(event,message):
    print(f'[BACKGROUND NOTIFICATION] {event}: {message}')
