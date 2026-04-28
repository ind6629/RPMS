-- RPMS 演示数据脚本（MySQL）
-- 使用前请确认已存在基础用户与房产数据（如 owner001~owner010、emp01~emp05）
-- 建议在测试库执行

START TRANSACTION;

-- 1) 财务：收费项目
INSERT INTO finance_charge_item (name, type, unit_price, unit, description, is_active, created_at, updated_at)
VALUES
('物业基础服务费', 'property_fee', 2.80, '元/㎡', '按建筑面积计费', 1, NOW(), NOW()),
('公共能耗分摊', 'other', 36.00, '元/户', '公共区域照明与电梯能耗分摊', 1, NOW(), NOW()),
('车位管理费', 'parking_fee', 120.00, '元/月', '地上固定车位月度管理', 1, NOW(), NOW());

-- 2) 财务：账单（演示生成 2026-04）
INSERT INTO finance_bill
    (property_id, charge_item_id, year_month, amount, status, due_date, paid_at, remark, created_at, updated_at)
SELECT
    p.id,
    ci.id,
    '2026-04',
    CASE
        WHEN ci.type = 'property_fee' THEN ROUND(IFNULL(p.area, 90) * ci.unit_price, 2)
        ELSE ci.unit_price
    END AS amount,
    'unpaid',
    '2026-04-30',
    NULL,
    '演示账单',
    NOW(),
    NOW()
FROM sys_property p
JOIN finance_charge_item ci ON ci.name IN ('物业基础服务费', '公共能耗分摊')
WHERE p.property_type = 'room'
  AND p.owner_id IS NOT NULL
LIMIT 40;

-- 3) 工单：批量补充演示工单
INSERT INTO property_repair_order
    (property_id, user_id, description, images, status, assigned_to_id, assigned_at, completed_at, remark, created_at, updated_at)
SELECT
    p.id,
    p.owner_id,
    CONCAT('演示报修：', p.building_number, '-', p.unit_number, '-', p.room_number, ' 卫浴渗水问题'),
    JSON_ARRAY(),
    'processing',
    (
      SELECT u.id FROM sys_user u
      WHERE u.role = 'employee' AND u.status = 1
      ORDER BY u.id
      LIMIT 1
    ),
    NOW(),
    NULL,
    '已派单，待上门处理',
    NOW(),
    NOW()
FROM sys_property p
WHERE p.property_type = 'room'
  AND p.owner_id IS NOT NULL
LIMIT 20;

-- 4) 投诉：补充演示投诉
INSERT INTO property_complaint
    (user_id, type, title, description, images, status, handler_id, handler_remark, completed_at, created_at, updated_at)
SELECT
    u.id,
    'environment',
    CONCAT('演示投诉-公共区域卫生（', u.username, '）'),
    '楼道垃圾清理频次偏低，异味较明显，建议增加保洁频次。',
    JSON_ARRAY(),
    'processing',
    (
      SELECT a.id FROM sys_user a
      WHERE a.role = 'admin'
      ORDER BY a.id
      LIMIT 1
    ),
    '已转保洁主管跟进',
    NULL,
    NOW(),
    NOW()
FROM sys_user u
WHERE u.role = 'owner'
ORDER BY u.id
LIMIT 12;

-- 5) 公告：补充演示公告
INSERT INTO operation_announcement
    (title, content, type, is_published, publish_time, is_withdrawn, is_archived, created_at, updated_at)
VALUES
('关于四月设备巡检的通知', '物业将于本周进行消防与电梯例行巡检，请住户配合。', 'notice', 1, NOW(), 0, 0, NOW(), NOW()),
('周末社区便民活动预告', '本周六上午开展便民义诊与家电小修活动，欢迎报名参与。', 'activity', 1, NOW(), 0, 0, NOW(), NOW()),
('暴雨天气安全提醒', '近期强降雨频繁，请注意阳台排水与地下车库通行安全。', 'urgent', 1, NOW(), 0, 0, NOW(), NOW());

-- 6) 系统日志：补充演示日志
INSERT INTO operation_system_log (user_id, action, detail, ip_address, created_at)
SELECT
    u.id,
    'demo_seed',
    CONCAT('演示数据写入完成，操作者：', u.username),
    '127.0.0.1',
    NOW()
FROM sys_user u
WHERE u.role = 'admin'
ORDER BY u.id
LIMIT 1;

COMMIT;

-- 回滚请手动执行：ROLLBACK;
