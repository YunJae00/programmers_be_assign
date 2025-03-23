from datetime import time

# 예약 기간
RESERVATION_MIN_DAYS_BEFORE = 3  # 예약은 최소 3일 전까지만 가능

# 운영 시간
OPERATION_START_TIME = time(9, 0)
OPERATION_END_TIME = time(18, 0)

# 동 시간대 최대 인원
MAX_ATTENDEES_PER_TIMESLOT = 50000