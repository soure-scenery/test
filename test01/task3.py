from redis.cluster import RedisCluster,ClusterNode
import time

SID = "12403030115"
prefix = f"exam:{SID}:"
S=15
C=S%5
score_self = 70 + C

#集群连接，替换为你的集群节点
r = RedisCluster(startup_nodes=[ClusterNode("127.0.0.1",30115)], decode_responses=True)

def q1_hash_student():
    print("====Q1学生信息Hash====")
    hkey = prefix + "student"
    r.delete(hkey)
    # hmset写入hash
    r.hset(hkey, mapping={
        "studentId":SID,
        "name":"张三",
        "className":"124030301",
        "courseId":f"COURSE‑{SID}‑01",
        "status":"learning"
    })
    #修改status为completed
    r.hset(hkey,"status","completed")
    #读取name status
    name = r.hget(hkey,"name")
    stat = r.hget(hkey,"status")
    print(f"name={name}, status={stat}")
    full_hash = r.hgetall(hkey)
    print("完整hash：",full_hash)

def q2_set_chapter():
    print("\n====Q2已完成章节Set====")
    skey = prefix + "chap_done"
    r.delete(skey)
    submit_list = ["CH01","CH02","CH02","CH03"]
    for item in submit_list:
        r.sadd(skey,item)
        cnt = r.scard(skey)
        print(f"提交 {item} 后已完成章节数量={cnt}")
    all_mem = r.smembers(skey)
    print("全部章节：",all_mem)
    print(f"CH02是否完成 {r.sismember(skey,'CH02')}")
    print(f"CH04是否完成 {r.sismember(skey,'CH04')}")

def q3_zset_rank():
    print("\n====Q3成绩排行榜 ZSet====")
    zk = prefix + "score_rank"
    r.delete(zk)
    members = {
        f"Student:{SID}": score_self,
        "demo:01":85,
        "demo:02":90,
        "demo:03":60,
        "demo:04":80
    }
    r.zadd(zk,members)
    #前3名从高到低 WITHSCORES
    top3 = r.zrange(zk,0,2,desc=True,withscores=True)
    print("更新前Top3：",top3)
    #本人分数增加20
    r.zincrby(zk,20,f"Student:{SID}")
    top3_2 = r.zrange(zk,0,2,desc=True,withscores=True)
    print("加分后Top3：",top3_2)
    myscore = r.zscore(zk,f"Student:{SID}")
    myrank_0 = r.zrevrank(zk,f"Student:{SID}")
    myrank = myrank_0 + 1
    print(f"本人更新后分数：{myscore}，名次：第{myrank}名")

def q4_session_ttl():
    print("\n====Q4会话生命周期 String 5秒过期====")
    skey = prefix + "session"
    r.setex(skey,5,"my‑session‑id‑abc123")
    val = r.get(skey)
    ttl = r.ttl(skey)
    print(f"刚创建值={val},TTL={ttl}")
    print("等待6秒...")
    time.sleep(6)
    exist = r.exists(skey)
    ttl2 = r.ttl(skey)
    print(f"sleep6s后键是否存在{exist},ttl={ttl2}")
    if exist ==0:
        print("过期验证通过")
    else:
        print("过期验证失败")

def q5_type_check():
    print("\n====Q5数据类型核验====")
    hk = prefix+"student"
    sk = prefix+"chap_done"
    zk = prefix+"score_rank"
    stk = prefix+"session"
    t_hash = r.type(hk)
    t_set = r.type(sk)
    t_zset = r.type(zk)
    t_str = r.type(stk)
    print(f"Hash student type:{t_hash}")
    print(f"Set chap_done type:{t_set}")
    print(f"ZSet score_rank type:{t_zset}")
    print(f"String session type:{t_str}")
    print("""
选择理由：
Hash：适合存储对象，多个字段，可单独读写某字段，适合学生多属性信息；
Set：无序集合自动去重，适合已完成章节，重复提交不会新增；
Sorted Set：带分数排序，适合排行榜，支持按分数范围、排名查询；
String：简单K‑V，适合会话字符串，原生支持expire设置过期时间。
""")

if __name__ == "__main__":
    q1_hash_student()
    q2_set_chapter()
    q3_zset_rank()
    q4_session_ttl()
    q5_type_check()
