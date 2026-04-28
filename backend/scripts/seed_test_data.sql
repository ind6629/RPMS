-- =============================================================================
-- RPMS 测试数据种子脚本（SQLite / Django 默认 db.sqlite3）
-- =============================================================================
-- 使用前请：
--   1. 已执行 python manage.py migrate
--   2. 建议先备份数据库文件 backend/db.sqlite3
--   3. 在 backend 目录执行：sqlite3 db.sqlite3 < scripts/seed_test_data.sql
--      或在 DB 客户端中打开 db.sqlite3 后整文件执行
--
-- 统一测试密码：Test123456（与 Django pbkdf2_sha256 算法一致）
--
-- 种子数据使用的 ID 区间（避免与少量手工数据冲突；若冲突请先调整或清空）：
--   用户 50000–50099 | 房产 51000–51999 | 收费项 60001–60009
--   账单 61000+      | 报修 62000+      | 投诉 63000+
--   反馈 64000+      | 公告 65000+      | 日志 66000+
--
-- 清理种子数据（按依赖倒序，在 sqlite3 中执行）见文件末尾 DELETE 段注释。
-- =============================================================================

PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- ---------------------------------------------------------------------------
-- 用户（sys_user）
-- 字段与 Django 迁移一致；布尔用 0/1
-- ---------------------------------------------------------------------------
INSERT OR REPLACE INTO sys_user (
  id, password, last_login, is_superuser, username, first_name, last_name,
  email, is_staff, is_active, date_joined, role, phone, avatar, status,
  created_at, updated_at
) VALUES
-- 管理员（可同时登录 Django Admin）
(50000, 'pbkdf2_sha256$600000$ABCDEFGHIJabcdefghij12$Xa4UdPildzxSs2sjyXWVLqj1Q8aD0RJIxx6S14S8Zts=', NULL, 1,
 'demo_admin', '', '', 'admin@demo.local', 1, 1, '2026-01-01 08:00:00',
 'admin', '13800000000', NULL, 1, '2026-01-01 08:00:00', '2026-01-01 08:00:00'),
-- 员工（用于工单自动分配）
(50001, 'pbkdf2_sha256$600000$ABCDEFGHIJabcdefghij12$Xa4UdPildzxSs2sjyXWVLqj1Q8aD0RJIxx6S14S8Zts=', NULL, 0,
 'demo_emp_01', '', '', 'emp01@demo.local', 0, 1, '2026-01-01 08:00:00',
 'employee', '13800000001', NULL, 1, '2026-01-01 08:00:00', '2026-01-01 08:00:00'),
(50002, 'pbkdf2_sha256$600000$ABCDEFGHIJabcdefghij12$Xa4UdPildzxSs2sjyXWVLqj1Q8aD0RJIxx6S14S8Zts=', NULL, 0,
 'demo_emp_02', '', '', 'emp02@demo.local', 0, 1, '2026-01-01 08:00:00',
 'employee', '13800000002', NULL, 1, '2026-01-01 08:00:00', '2026-01-01 08:00:00'),
(50003, 'pbkdf2_sha256$600000$ABCDEFGHIJabcdefghij12$Xa4UdPildzxSs2sjyXWVLqj1Q8aD0RJIxx6S14S8Zts=', NULL, 0,
 'demo_emp_03', '', '', 'emp03@demo.local', 0, 1, '2026-01-01 08:00:00',
 'employee', '13800000003', NULL, 1, '2026-01-01 08:00:00', '2026-01-01 08:00:00'),
(50004, 'pbkdf2_sha256$600000$ABCDEFGHIJabcdefghij12$Xa4UdPildzxSs2sjyXWVLqj1Q8aD0RJIxx6S14S8Zts=', NULL, 0,
 'demo_emp_04', '', '', 'emp04@demo.local', 0, 1, '2026-01-01 08:00:00',
 'employee', '13800000004', NULL, 1, '2026-01-01 08:00:00', '2026-01-01 08:00:00'),
(50005, 'pbkdf2_sha256$600000$ABCDEFGHIJabcdefghij12$Xa4UdPildzxSs2sjyXWVLqj1Q8aD0RJIxx6S14S8Zts=', NULL, 0,
 'demo_emp_05', '', '', 'emp05@demo.local', 0, 1, '2026-01-01 08:00:00',
 'employee', '13800000005', NULL, 1, '2026-01-01 08:00:00', '2026-01-01 08:00:00');

-- 业主 demo_owner_01 .. demo_owner_40（密码同上）
INSERT OR REPLACE INTO sys_user (
  id, password, last_login, is_superuser, username, first_name, last_name,
  email, is_staff, is_active, date_joined, role, phone, avatar, status,
  created_at, updated_at
)
SELECT
  50010 + (n - 1),
  'pbkdf2_sha256$600000$ABCDEFGHIJabcdefghij12$Xa4UdPildzxSs2sjyXWVLqj1Q8aD0RJIxx6S14S8Zts=',
  NULL,
  0,
  printf('demo_owner_%02d', n),
  '',
  '',
  printf('owner%02d@demo.local', n),
  0,
  1,
  '2026-01-01 09:00:00',
  'owner',
  printf('139%07d', 1000000 + n),
  NULL,
  1,
  '2026-01-01 09:00:00',
  '2026-01-01 09:00:00'
FROM (
  WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 40)
  SELECT n FROM seq
);

-- ---------------------------------------------------------------------------
-- 用户详情（可选）
-- ---------------------------------------------------------------------------
INSERT OR REPLACE INTO sys_user_profile (id, gender, id_card, address, emergency_contact, emergency_phone, user_id)
SELECT
  70000 + n,
  CASE WHEN n % 2 = 1 THEN 'male' ELSE 'female' END,
  printf('110101199001%05d', n),
  printf('测试小区%d号楼', (n % 5) + 1),
  '紧急联系人',
  '13700000000',
  50010 + (n - 1)
FROM (
  WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n <= 40)
  SELECT n FROM seq
);

-- ---------------------------------------------------------------------------
-- 房产：2 栋 → 每栋 2 单元 → 每单元 10 套 = 40 套，对应 40 位业主
-- ---------------------------------------------------------------------------
-- 楼栋
INSERT OR REPLACE INTO sys_property (
  id, name, property_type, parent_id, building_number, unit_number, room_number,
  area, owner_id, status, created_at, updated_at
) VALUES
(51001, '测试A栋', 'building', NULL, 'A', '', '', NULL, NULL, 1, '2026-01-01 10:00:00', '2026-01-01 10:00:00'),
(51002, '测试B栋', 'building', NULL, 'B', '', '', NULL, NULL, 1, '2026-01-01 10:00:00', '2026-01-01 10:00:00');

-- 单元（A 栋 1、2 单元；B 栋 1、2 单元）
INSERT OR REPLACE INTO sys_property (
  id, name, property_type, parent_id, building_number, unit_number, room_number,
  area, owner_id, status, created_at, updated_at
) VALUES
(51101, 'A栋1单元', 'unit', 51001, 'A', '1', '', NULL, NULL, 1, '2026-01-01 10:00:00', '2026-01-01 10:00:00'),
(51102, 'A栋2单元', 'unit', 51001, 'A', '2', '', NULL, NULL, 1, '2026-01-01 10:00:00', '2026-01-01 10:00:00'),
(51103, 'B栋1单元', 'unit', 51002, 'B', '1', '', NULL, NULL, 1, '2026-01-01 10:00:00', '2026-01-01 10:00:00'),
(51104, 'B栋2单元', 'unit', 51002, 'B', '2', '', NULL, NULL, 1, '2026-01-01 10:00:00', '2026-01-01 10:00:00');

-- 房屋（id 52001–52040），业主 50010–50049
INSERT OR REPLACE INTO sys_property (
  id, name, property_type, parent_id, building_number, unit_number, room_number,
  area, owner_id, status, created_at, updated_at
)
SELECT
  52000 + n,
  printf('%s栋%s单元%03d', CASE WHEN n <= 20 THEN 'A' ELSE 'B' END,
         CASE WHEN n <= 10 THEN '1' WHEN n <= 20 THEN '2' WHEN n <= 30 THEN '1' ELSE '2' END,
         100 + ((n - 1) % 10) + 1),
  'room',
  CASE
    WHEN n <= 10 THEN 51101
    WHEN n <= 20 THEN 51102
    WHEN n <= 30 THEN 51103
    ELSE 51104
  END,
  CASE WHEN n <= 20 THEN 'A' ELSE 'B' END,
  CASE WHEN n <= 10 THEN '1' WHEN n <= 20 THEN '2' WHEN n <= 30 THEN '1' ELSE '2' END,
  printf('%03d', 100 + ((n - 1) % 10) + 1),
  75.0 + (n % 15) + 0.5 * (n % 3),
  50010 + (n - 1),
  1,
  '2026-01-01 10:30:00',
  '2026-01-01 10:30:00'
FROM (
  WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n <= 40)
  SELECT n FROM seq
);

-- ---------------------------------------------------------------------------
-- 收费项目
-- ---------------------------------------------------------------------------
INSERT OR REPLACE INTO finance_charge_item (
  id, name, type, unit_price, unit, description, is_active, created_at, updated_at
) VALUES
(60001, '住宅物业费', 'property_fee', 2.80, '元/㎡·月', '种子数据-物业费', 1, '2026-01-01 11:00:00', '2026-01-01 11:00:00'),
(60002, '地下车位管理费', 'parking_fee', 120.00, '元/月', '种子数据-停车费', 1, '2026-01-01 11:00:00', '2026-01-01 11:00:00'),
(60003, '代收水费', 'water_fee', 3.50, '元/吨', '种子数据-水费', 1, '2026-01-01 11:00:00', '2026-01-01 11:00:00');

-- ---------------------------------------------------------------------------
-- 账单（每套房 2026-03、2026-04 两期物业费；部分已缴）
-- unique (property_id, charge_item_id, year_month)
-- ---------------------------------------------------------------------------
INSERT OR REPLACE INTO finance_bill (
  id, property_id, charge_item_id, year_month, amount, status, due_date,
  paid_at, remark, created_at, updated_at
)
SELECT
  61000 + (n - 1) * 2 + 1,
  52000 + n,
  60001,
  '2026-03',
  ROUND((75.0 + (n % 15)) * 2.80, 2),
  CASE WHEN n % 4 = 0 THEN 'unpaid' ELSE 'paid' END,
  '2026-03-31',
  CASE WHEN n % 4 = 0 THEN NULL ELSE '2026-03-15 10:00:00' END,
  'SEED_BILL',
  '2026-02-01 09:00:00',
  '2026-02-01 09:00:00'
FROM (
  WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n <= 40)
  SELECT n FROM seq
);

INSERT OR REPLACE INTO finance_bill (
  id, property_id, charge_item_id, year_month, amount, status, due_date,
  paid_at, remark, created_at, updated_at
)
SELECT
  61000 + (n - 1) * 2 + 2,
  52000 + n,
  60001,
  '2026-04',
  ROUND((75.0 + (n % 15)) * 2.80, 2),
  CASE WHEN n % 3 = 0 THEN 'paid' WHEN n % 3 = 1 THEN 'unpaid' ELSE 'overdue' END,
  '2026-04-30',
  CASE WHEN n % 3 = 0 THEN '2026-04-10 11:00:00' ELSE NULL END,
  'SEED_BILL',
  '2026-04-01 09:00:00',
  '2026-04-01 09:00:00'
FROM (
  WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n <= 40)
  SELECT n FROM seq
);

-- 部分已缴账单的缴费记录（id 与 bill_id 一一对应，便于重复执行）
INSERT OR REPLACE INTO finance_payment_record (
  id, bill_id, amount, payment_method, transaction_no, payment_time, operator_id, remark
)
SELECT
  900000 + id,
  id,
  amount,
  'wechat',
  printf('SEED-WX-%d', id),
  IFNULL(paid_at, created_at),
  50000,
  'SEED_PAY'
FROM finance_bill
WHERE status = 'paid' AND remark = 'SEED_BILL';

-- ---------------------------------------------------------------------------
-- 报修工单（多种状态，部分已指派员工）
-- ---------------------------------------------------------------------------
INSERT OR REPLACE INTO property_repair_order (
  id, property_id, user_id, description, images, status, assigned_to_id,
  assigned_at, completed_at, remark, created_at, updated_at
)
SELECT
  63000 + n,
  52000 + ((n - 1) % 40) + 1,
  50010 + ((n - 1) % 40),
  printf('【种子报修】%d 号工单：管道/照明/门窗等故障描述用于压力测试。', n),
  '[]',
  CASE
    WHEN n % 5 = 1 THEN 'pending'
    WHEN n % 5 = 2 THEN 'processing'
    WHEN n % 5 = 3 THEN 'processing'
    WHEN n % 5 = 4 THEN 'completed'
    ELSE 'cancelled'
  END,
  CASE
    WHEN n % 5 IN (2, 3) THEN 50001 + ((n - 1) % 5)
    ELSE NULL
  END,
  CASE WHEN n % 5 IN (2, 3) THEN printf('2026-04-%02d 09:00:00', 1 + (n % 28)) ELSE NULL END,
  CASE WHEN n % 5 = 4 THEN printf('2026-04-%02d 18:00:00', 2 + (n % 27)) ELSE NULL END,
  CASE WHEN n % 5 = 4 THEN '已现场处理' ELSE '' END,
  printf('2026-03-%02d 08:30:00', 1 + (n % 28)),
  '2026-04-11 12:00:00'
FROM (
  WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n <= 60)
  SELECT n FROM seq
);

-- ---------------------------------------------------------------------------
-- 服务反馈（仅对已完工工单，一对一；从报修表中取前 15 条已完成）
-- ---------------------------------------------------------------------------
INSERT OR REPLACE INTO property_service_feedback (id, order_id, rating, comment, created_at)
SELECT
  640000 + r.id,
  r.id,
  3 + (ABS(r.id) % 3),
  printf('服务态度%s（种子数据）', CASE (ABS(r.id) % 3) WHEN 0 THEN '满意' WHEN 1 THEN '尚可' ELSE '一般' END),
  '2026-04-05 20:00:00'
FROM property_repair_order AS r
WHERE r.status = 'completed'
  AND r.id BETWEEN 63001 AND 63099
ORDER BY r.id
LIMIT 15;

-- ---------------------------------------------------------------------------
-- 投诉建议
-- ---------------------------------------------------------------------------
INSERT OR REPLACE INTO property_complaint (
  id, user_id, type, title, description, images, status, handler_id,
  handler_remark, completed_at, created_at, updated_at
)
SELECT
  65000 + n,
  50010 + ((n - 1) % 40),
  (CASE (n % 5) WHEN 0 THEN 'service' WHEN 1 THEN 'environment' WHEN 2 THEN 'security' WHEN 3 THEN 'facility' ELSE 'other' END),
  printf('投诉建议标题 #%d', n),
  printf('详细描述：楼道卫生/噪音/设施等测试内容 %d', n),
  '[]',
  (CASE (n % 3) WHEN 0 THEN 'pending' WHEN 1 THEN 'processing' ELSE 'completed' END),
  CASE WHEN n % 3 = 2 THEN 50000 ELSE NULL END,
  CASE WHEN n % 3 = 2 THEN '已电话沟通并安排整改' ELSE '' END,
  CASE WHEN n % 3 = 2 THEN '2026-04-08 17:00:00' ELSE NULL END,
  printf('2026-03-%02d 14:00:00', 1 + (n % 25)),
  '2026-04-11 12:00:00'
FROM (
  WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n <= 35)
  SELECT n FROM seq
);

-- ---------------------------------------------------------------------------
-- 公告
-- ---------------------------------------------------------------------------
INSERT OR REPLACE INTO operation_announcement (
  id, title, content, type, is_published, publish_time, is_withdrawn, is_archived,
  created_at, updated_at
) VALUES
(66001, '关于清明节期间装修静音的通知', '尊敬的业主：4月4日至6日暂停有声施工……', 'notice', 1, '2026-03-20 08:00:00', 0, 0, '2026-03-18 10:00:00', '2026-03-18 10:00:00'),
(66002, '小区春季消杀安排', '本周三上午对公共区域进行消杀……', 'notice', 1, '2026-04-01 00:00:00', 0, 0, '2026-03-28 15:00:00', '2026-03-28 15:00:00'),
(66003, '停水演练（测试-未发布草稿）', '此为草稿公告，前台不应展示。', 'urgent', 0, NULL, 0, 0, '2026-04-10 09:00:00', '2026-04-10 09:00:00'),
(66004, '亲子活动报名', '周六下午中心花园亲子活动……', 'activity', 1, '2026-04-15 09:00:00', 0, 0, '2026-04-05 11:00:00', '2026-04-05 11:00:00'),
(66005, '已撤回公告示例', '本条已撤回。', 'notice', 1, '2026-01-01 00:00:00', 1, 0, '2025-12-01 10:00:00', '2025-12-02 10:00:00');

INSERT OR REPLACE INTO operation_announcement (
  id, title, content, type, is_published, publish_time, is_withdrawn, is_archived,
  created_at, updated_at
)
SELECT
  66100 + n,
  printf('系统通知 #%d', n),
  printf('这是一条批量生成的公告内容，用于列表与分页测试。编号 %d。', n),
  CASE n % 3 WHEN 0 THEN 'notice' WHEN 1 THEN 'activity' ELSE 'urgent' END,
  1,
  printf('2026-04-%02d 08:00:00', 1 + (n % 28)),
  0,
  0,
  '2026-04-01 12:00:00',
  '2026-04-01 12:00:00'
FROM (
  WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n <= 25)
  SELECT n FROM seq
);

-- ---------------------------------------------------------------------------
-- 系统日志
-- ---------------------------------------------------------------------------
INSERT OR REPLACE INTO operation_system_log (id, user_id, action, detail, ip_address, created_at)
SELECT
  67000 + n,
  CASE WHEN n % 5 = 0 THEN NULL ELSE 50000 + (n % 6) END,
  printf('seed_action_%d', n % 7),
  printf('种子日志详情 #%d', n),
  printf('192.168.1.%d', (n % 200) + 1),
  printf('2026-04-%02d %02d:%02d:00', 1 + (n % 28), (n * 3) % 24, (n * 7) % 60)
FROM (
  WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n <= 80)
  SELECT n FROM seq
);

COMMIT;

PRAGMA foreign_keys = ON;

-- =============================================================================
-- 可选：清理本脚本插入的数据（按依赖倒序；执行前请确认 ID 区间无业务数据）
-- =============================================================================
-- DELETE FROM operation_system_log WHERE id BETWEEN 67000 AND 67999;
-- DELETE FROM operation_announcement WHERE id BETWEEN 66001 AND 66200;
-- DELETE FROM property_complaint WHERE id BETWEEN 65000 AND 65099;
-- DELETE FROM property_service_feedback WHERE id BETWEEN 64000 AND 64099;
-- DELETE FROM property_repair_order WHERE id BETWEEN 63000 AND 63099;
-- DELETE FROM finance_payment_record WHERE remark = 'SEED_PAY' OR id >= 900000;
-- DELETE FROM finance_bill WHERE remark = 'SEED_BILL';
-- DELETE FROM finance_charge_item WHERE id BETWEEN 60001 AND 60009;
-- DELETE FROM sys_property WHERE id BETWEEN 51001 AND 52999;
-- DELETE FROM sys_user_profile WHERE id BETWEEN 70000 AND 70999;
-- DELETE FROM sys_user WHERE id BETWEEN 50000 AND 50099;
-- =============================================================================
-- MySQL 使用说明（若 DJANGO_USE_SQLITE=0）：
--   - 表名、字段名与上相同；布尔改为 1/0 或 TRUE/FALSE 均可
--   - JSON 列 images 仍可用 '[]' 字符串（MySQL 5.7+ JSON）
--   - 自增：导入后可能需要调整各表 AUTO_INCREMENT
--   - 建议优先使用本项目的 manage.py loaddata 或自定义 management 命令迁移数据
-- =============================================================================
