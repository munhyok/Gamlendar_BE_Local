from redis_om import get_redis_connection, HashModel, JsonModel, Migrator, EmbeddedJsonModel, Field
import redis

reCache = redis.StrictRedis(host='localhost', port=6379, db = 0, decode_responses=True)