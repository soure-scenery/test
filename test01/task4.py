from redis.cluster import RedisCluster,ClusterNode
import time

SID = "12403030115"
prefix = f"exam:{SID}:"
S=15
C=S%5
N = 1000 + 100*C + S
Q =100
print(f"N={N},每批Q={Q}")

r = RedisCluster(startup_nodes=[ClusterNode("127.0.0.1",30115)], decode_responses=True)

def clear_keys甲乙():
    for i in range(1,N+1):
        r.delete(f"{prefix}seq:{i}")
        r.delete(f"{prefix}pipe:{i}")

def caseA_one_by_one():
    """方案甲：逐条写入，等待返回再下一条，无pipeline"""
    start = time.time()*1000
    for i in range(1,N+1):
        k = f"{prefix}seq:{i}"
        v = f"value-{SID}-{i}"
        r.set(k,v)
    end = time.time()*1000
    cost = int(end - start)
    return cost

def caseB_pipeline_batch():
    """方案乙 pipeline，每批最多100，transaction=False，不包装事务"""
    start = time.time()*1000
    batch_num = 0
    last_batch_size =0
    pipe = r.pipeline(transaction=False)
    for idx in range(1,N+1):
        pipe.set(f"{prefix}pipe:{idx}",f"value-{SID}-{idx}")
        if idx % Q == 0:
            batch_num +=1
            pipe.execute()
            pipe.reset()
    #处理最后一批剩余
    remain = N % Q
    if remain>0:
        last_batch_size = remain
        pipe.execute()
    else:
        last_batch_size = Q
    end = time.time()*1000
    cost = int(end-start)
    if remain ==0:
        last_batch_size = Q
    return cost,batch_num,last_batch_size

if __name__ == "__main__":
    clear_keys甲乙()
    costA = caseA_one_by_one()
    costB,batches,lastcnt = caseB_pipeline_batch()
    print(f"""
====结果表格====
命令总数:{N}
Pipeline批次数:{batches}
最后一批数量:{lastcnt}
方案甲耗时(ms):{costA}
方案乙耗时(ms):{costB}
""")
    print("结论：Pipeline方案乙一般更快。")
    print("""
如果Pipeline不比逐条快甚至更慢的可能原因：
1.测试数据量太小，网络/函数调用开销占主导；
2.本地Redis，网络延迟几乎为0，Pipeline优势体现不出来；
3.pipeline批次设置过小，大量小批次；
4.客户端、集群内部重定向带来额外开销。
""")
