from pymongo import MongoClient
from pprint import pprint

SID = "12403030115"
S = 15
A = S % 3
client = MongoClient("mongodb://localhost:27017")
db = client[f"exam_{SID}"]
coll = db["courses"]

# ========== 初始化数据，只运行一次 ==========
def init_data():
    coll.delete_many({})
    docs = [
        {
            "_id": f"COURSE-{SID}-01",
            "title": "NoSQL数据库",
            "teacher": "张老师",
            "status": "OPEN",
            "chapters": [
                {"chapterId": "CH01", "title": "MongoDB基础", "hours": 2},
                {"chapterId": "CH02", "title": "Redis基础", "hours": 2}
            ]
        },
        {
            "_id": f"COURSE-{SID}-02",
            "title": "数据库原理",
            "teacher": "张老师",
            "status": "CLOSED",
            "chapters": [{"chapterId": "CH01", "title": "关系模型", "hours": 2}]
        },
        {
            "_id": f"COURSE-{SID}-03",
            "title": "机器学习",
            "teacher": "李老师",
            "status": "OPEN",
            "chapters": [
                {"chapterId": "CH01", "title": "分类", "hours": 2},
                {"chapterId": "CH02", "title": "聚类", "hours": 2}
            ]
        }
    ]
    coll.insert_many(docs)
    print("===初始化完成===")

def q1_query_course():
    """1 查询张老师 OPEN课程，输出课程编号、课程名称、章节数量"""
    res = coll.find({"teacher":"张老师","status":"OPEN"})
    print("\n====Q1 查询结果====")
    for doc in res:
        cid = doc["_id"]
        title = doc["title"]
        ch_cnt = len(doc["chapters"])
        print(f"课程编号:{cid},课程名称:{title},章节数量:{ch_cnt}")

def q2_update_chapter():
    """2 修改01课程CH02标题 Redis基础与应用‑S S=15"""
    cid = f"COURSE-{SID}-01"
    new_title = f"Redis基础与应用-{S}"
    # 局部更新 $set 数组指定下标
    ret = coll.update_one(
        {"_id": cid, "chapters.chapterId":"CH02"},
        {"$set":{"chapters.$.title": new_title}}
    )
    print("\n====Q2更新返回结果===")
    print(f"matched_count={ret.matched_count}, modified_count={ret.modified_count}")
    updated_doc = coll.find_one({"_id":cid})
    pprint(updated_doc)

def q3_add_chapter_safe():
    """3 增加CH03，防止重复，不能整体替换文档；hours=2+A A=0 →2"""
    cid = f"COURSE-{SID}-01"
    new_ch = {"chapterId":"CH03","title":"Redis高级操作","hours":2+A}
    # $addToSet 数组添加，元素不重复，局部更新
    update_cmd = {
        "$addToSet":{
            "chapters": new_ch
        }
    }
    # 连续执行两次
    for idx in range(2):
        ret = coll.update_one({"_id":cid}, update_cmd)
        print(f"\nQ3第{idx+1}次执行 matched={ret.matched_count},modified={ret.modified_count}")

def q4_check_explain():
    """4 验证输出+解释"""
    cid = f"COURSE-{SID}-01"
    doc = coll.find_one({"_id":cid})
    ch02_title = None
    ch03_count = 0
    total_ch = len(doc["chapters"])
    for ch in doc["chapters"]:
        if ch["chapterId"] == "CH02":
            ch02_title = ch["title"]
        if ch["chapterId"] == "CH03":
            ch03_count +=1
    teacher_val = doc["teacher"]
    status_val = doc["status"]
    print("\n====Q4核验结果====")
    print(f"(1) CH02标题：{ch02_title}")
    print(f"(2) CH03数量：{ch03_count}")
    print(f"(3) 最终章节总数：{total_ch}")
    print(f"(4) teacher={teacher_val}, status={status_val}")
    print("teacher和status保持原值：", teacher_val=="张老师" and status_val=="OPEN")
    print("""
【解释为什么适合局部更新，不宜替换整个文档】
局部更新($set/$addToSet)仅修改需要改动的字段/数组元素，不需要把完整文档拉到客户端修改再写回。
1.减少网络IO，只传输修改部分；
2.避免客户端修改‑全量替换带来的并发覆盖丢失更新问题；
3.服务端直接执行更新逻辑，保证原子性；
4.其他字段不受影响，不需要重新赋值全部字段。
""")

if __name__ == "__main__":
    init_data()
    q1_query_course()
    q2_update_chapter()
    q3_add_chapter_safe()
    q4_check_explain()
