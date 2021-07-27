import json
import time
import urllib3


def lambda_handler(event, context):
     req_type: str = event.get('queryStringParameters', {}).get('req_type', '')

     if req_type.__eq__("entry"):
          plate: str = event.get('queryStringParameters', {}).get('plate', '')
          parkingLot: int = event.get('queryStringParameters', {}).get('parkingLot', '')
          entry_timestamp: int = int(event.get('queryStringParameters', {}).get('timestamp', '-1'))

          if entry_timestamp == -1:
               entry_timestamp = int(time.time())

          ticketId = f'{entry_timestamp}_{parkingLot}_{plate}'

          url = f'http://live-test.ravendb.net/databases/parking/docs?id={ticketId}'

          data = json.dumps({
               'ticketId': ticketId,
               'entry_timestamp': entry_timestamp,
               'plate': plate,
               'parkingLot': parkingLot,
               'paid': False
          })

          urllib3.PoolManager().request('PUT',
                                        url,
                                        body=data)

          return {
               "statusCode": 200,
               "headers": {
                    "Content-Type": "application/json"
               },
               "body": json.dumps({"ticketId": ticketId})
          }
     elif req_type.__eq__("exit"):
          ticketId: str = event.get('queryStringParameters', {}).get('ticketId', '')
          exit_timestamp: int = int(event.get('queryStringParameters', {}).get('timestamp', '-1'))

          if len(ticketId) > 0:
               _s = ticketId.split('_')
               ts = int(_s[0])
               parking_lot = _s[1]
               plate = _s[2]

               if exit_timestamp == -1:
                    exit_timestamp = int(time.time())
               diff = exit_timestamp - ts

               price_hour = 10
               price_15_mins = price_hour / (60 / 15)

               charge = (diff // (60 * 15)) * price_15_mins

               return {
                    "statusCode": 200,
                    "headers": {
                         "Content-Type": "application/json"
                    },
                    'body': json.dumps({
                         "plate": plate,
                         "parked_time": f'{diff // 60} minutes and {diff % 60} seconds',
                         "parking_lot": parking_lot,
                         "charge": f'{charge}$'
                    })
               }
     return {
          'statusCode': 500,
          'body': "Internal Error"
     }
