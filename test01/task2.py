from pymongo import MongoClient
from pymongo.errors import PyMongoError
import uuid

SID = "12403030115"
S=15
A = S%3
C = S%5
Stock = 5 + C
Buy = 1 + A

client = MongoClient("mongodb://localhost:27017")
db = client[f"exam_{SID}"]
inv_coll = db["inventory"]
ord_coll = db["orders"]
BOOK_ID = f"BOOK-{SID}"

def reset_scenario(init_stock):
    """重置场景：清空集合，设置初始库存"""
    inv_coll.delete_many({})
    ord_coll.delete_many({})
    inv_coll.insert_one({
        "_id": BOOK_ID,
        "title": "NoSQL数据库教材",
        "stock": init_stock
    })

def atomic_deduct(buy_num):
    """Q1 原子扣减，单文档更新；条件：stock>=buy_num"""
    update_ret = inv_coll.update_one(
        {
            "_id": BOOK_ID,
            "stock": {"$gte": buy_num}
        },
        {"$inc":{"stock": -buy_num}}
    )
    return update_ret

def judge_result(ret):
    """Q2 判断结果返回状态码
    0:扣减成功
    1:库存不足或文档不存在
    2:异常
    """
    try:
        if ret.matched_count >= 1 and ret.modified_count >=1:
            return 0
        else:
            return 1
    except PyMongoError:
        return 2

def place_order(requestId, forceError:bool):
    """Q3 订购函数，事务；forceError=True中间抛异常"""
    session = client.start_session()
    try:
        with session.start_transaction():
            # 扣库存
            upd_ret = inv_coll.update_one(
                {"_id":BOOK_ID,"stock":{"$gte":Buy}},
                {"$inc":{"stock": -Buy}},
                session=session
            )
            if not (upd_ret.matched_count and upd_ret.modified_count):
                #扣减失败，直接返回，不生成订单
                return False
            if forceError:
                raise Exception("模拟中途异常")
            #插入订单
            ord_coll.insert_one({
                "_id": requestId,
                "bookId": BOOK_ID,
                "studentId": SID,
                "quantity": Buy
            },session=session)
            return True
    except Exception as e:
        return False
    finally:
        session.end_session()

def run_one_case(scene_name,init_stock,force_err=False,times=1):
    """执行一个测试场景 T1-T4"""
    reset_scenario(init_stock)
    succ=0
    fail=0
    for _ in range(times):
        rid = str(uuid.uuid4())
        ok = place_order(rid,force_err)
        if ok:
            succ +=1
        else:
            fail +=1
    inv_doc = inv_coll.find_one({"_id":BOOK_ID})
    final_stock = inv_doc["stock"] if inv_doc else 0
    order_cnt = ord_coll.count_documents({})
    passed = False
    #简单核验
    if scene_name == "T1":
        passed = (succ==1 and fail==0 and final_stock == init_stock - Buy and order_cnt ==1)
    elif scene_name == "T2":
        passed = (succ==0 and final_stock == init_stock and order_cnt==0)
    elif scene_name == "T3":
        passed = (succ==0 and final_stock == init_stock and order_cnt==0)
    elif scene_name == "T4":
        max_ok = init_stock // Buy
        passed = (succ == max_ok)
    print(f"""
====场景{scene_name}====
初始库存:{init_stock}
购买数量:{Buy}
成功次数:{succ}
失败次数:{fail}
最终库存:{final_stock}
订单数量:{order_cnt}
核验通过:{passed}
""")
    return succ,fail,final_stock,order_cnt,passed

if __name__ == "__main__":
    print(f"全局参数 Stock={Stock},Buy={Buy}")
    #T1正常订购
    run_one_case("T1",Stock,force_err=False,times=1)
    #T2库存不足，初始库存Buy-1
    run_one_case("T2",Buy-1,force_err=False,times=1)
    #T3中途异常 forceError=True
    run_one_case("T3",Stock,force_err=True,times=1)
    #T4连续购买 floor(Stock/Buy)+1次
    t4_times = (Stock//Buy)+1
    run_one_case("T4",Stock,force_err=False,times=t4_times)

    print("""
====Q5结果解释====
(1)单次扣减是单文档原子操作，但是订单是另一个集合的文档，属于多文档操作。单文档原子性不能跨多个集合；需要事务保证库存扣减和订单插入要么全部成功，要么全部回滚。
(2)forceError测试模拟业务中途报错；验证事务回滚能力：库存扣减执行之后、订单插入前抛出异常，事务回滚，库存恢复原值，不会产生订单，不会出现库存被扣减但是没有订单的不一致状态。
""")
