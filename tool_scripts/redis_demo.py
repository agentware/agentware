import json
import redis

# Establish a connection to the Redis server
redis_host = 'localhost'
redis_port = 6379
redis_db = 0
redis_password = None
redis_client = redis.Redis(
    host=redis_host, port=redis_port, db=redis_db, password=redis_password)

# Replace the existing dog list with a new dog list more efficiently using a Redis transaction
key = 'dogs'
new_dog_list = ['wooffy1', 'wooffy2',
                'wooffy3', 'wooffy4', 'wooffy5', 'wooffy6']

# Begin a Redis transaction
transaction = redis_client.pipeline()

# Store the new dog list in Redis
transaction.delete(key)  # Delete the existing key
for dog_name in new_dog_list:
    # Assuming each dog name is a dictionary with other attributes
    dog_data = {'name': dog_name}
    serialized_dog = json.dumps(dog_data)
    # Push each serialized dog to the list
    transaction.rpush(key, serialized_dog)

# Execute the Redis transaction
result = transaction.execute()
print(redis_client.getrange(key, 0, 3))
