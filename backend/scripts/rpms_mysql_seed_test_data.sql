-- =============================================================================
-- RPMS 住宅物业管理系统 - MySQL 测试数据种子脚本
-- =============================================================================
-- 使用前请确认：
-- 1. 已执行 python manage.py migrate（表结构已存在）
-- 2. MySQL 8.0+（使用存储过程与 JSON 类型）
-- 3. 修改下方 USE 为你的库名（与 settings.py 中 DB_NAME 一致）
--
-- 执行方式（示例）：
--   mysql -u root -p your_database < scripts/rpms_mysql_seed_test_data.sql
--
-- 登录说明（脚本插入的测试用户）：
--   统一密码：test123456
--   管理员：admin_demo
--   员工：emp01 ~ emp05
--   业主：owner001 ~ owner040
--
-- 警告：会清空下列业务表中的全部数据（不影响 django_migrations）：
--   sys_user / sys_user_profile / sys_property / property_* / finance_* /
--   operation_* / sys_user_groups / sys_user_user_permissions
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 数据库名
USE `property_management`;

-- Django 4.2 pbkdf2_sha256$600000$... 对应明文密码 test123456
SET @pwd := 'pbkdf2_sha256$600000$RPMS2026TestSalt00001$MEjH799RPgthkeqQXSZNJV87Tr8cEfIR8gjXGbv18oI=';

-- 清空业务数据（顺序：子表 -> 父表）
TRUNCATE TABLE `property_service_feedback`;
TRUNCATE TABLE `property_repair_order`;
TRUNCATE TABLE `property_complaint`;
TRUNCATE TABLE `finance_payment_record`;
TRUNCATE TABLE `finance_bill`;
TRUNCATE TABLE `finance_charge_item`;
TRUNCATE TABLE `operation_system_log`;
TRUNCATE TABLE `operation_announcement`;
TRUNCATE TABLE `sys_user_groups`;
TRUNCATE TABLE `sys_user_user_permissions`;
TRUNCATE TABLE `sys_user_profile`;
TRUNCATE TABLE `sys_property`;
TRUNCATE TABLE `sys_user`;

DROP PROCEDURE IF EXISTS `rpms_seed_demo`;

DELIMITER $$

CREATE PROCEDURE `rpms_seed_demo`()
BEGIN
  DECLARE v_b INT DEFAULT 1;
  DECLARE v_u INT;
  DECLARE v_r INT;
  DECLARE v_bid BIGINT;
  DECLARE v_uid BIGINT;
  DECLARE v_owner BIGINT;
  DECLARE v_room_count INT DEFAULT 0;
  DECLARE v_rid BIGINT;
  DECLARE v_ci1 BIGINT;
  DECLARE v_ci2 BIGINT;
  DECLARE v_i INT;
  DECLARE v_rep INT;
  DECLARE v_uid_complaint BIGINT;
  DECLARE v_room_total INT DEFAULT 0;
  DECLARE v_room_idx INT DEFAULT 0;

  -- ---------- 用户：1 管理员 + 5 员工 + 40 业主 ----------
  INSERT INTO `sys_user` (
    `id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`,
    `email`, `is_staff`, `is_active`, `date_joined`, `role`, `phone`, `avatar`, `status`, `created_at`, `updated_at`
  ) VALUES
  (1, @pwd, NULL, 1, 'admin_demo', '', '', 'admin@rpms.test', 1, 1, NOW(), 'admin', '13800000001', NULL, 1, NOW(), NOW());

  SET v_b = 2;
  WHILE v_b <= 6 DO
    INSERT INTO `sys_user` (
      `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`,
      `email`, `is_staff`, `is_active`, `date_joined`, `role`, `phone`, `avatar`, `status`, `created_at`, `updated_at`
    ) VALUES (
      @pwd, NULL, 0, CONCAT('emp', LPAD(v_b - 1, 2, '0')), '', '', CONCAT('emp', v_b - 1, '@rpms.test'),
      0, 1, NOW(), 'employee', CONCAT('1380000', LPAD(1000 + v_b, 4, '0')), NULL, 1, NOW(), NOW()
    );
    SET v_b = v_b + 1;
  END WHILE;

  SET v_b = 1;
  WHILE v_b <= 40 DO
    INSERT INTO `sys_user` (
      `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`,
      `email`, `is_staff`, `is_active`, `date_joined`, `role`, `phone`, `avatar`, `status`, `created_at`, `updated_at`
    ) VALUES (
      @pwd, NULL, 0, CONCAT('owner', LPAD(v_b, 3, '0')), '', '', CONCAT('owner', LPAD(v_b, 3, '0'), '@rpms.test'),
      0, 1, NOW(), 'owner', CONCAT('139', LPAD(1000000 + v_b, 7, '0')), NULL, 1, NOW(), NOW()
    );
    SET v_b = v_b + 1;
  END WHILE;

  ALTER TABLE `sys_user` AUTO_INCREMENT = 1000;

  -- ---------- 用户详情（每人一条）----------
  INSERT INTO `sys_user_profile` (`gender`, `id_card`, `address`, `emergency_contact`, `emergency_phone`, `user_id`)
  SELECT
    IF(`id` % 2 = 0, 'female', 'male'),
    CONCAT('11010119900101', LPAD(`id`, 4, '0')),
    CONCAT('测试小区虚拟地址-', `id`),
    '张联系人',
    '13700000000',
    `id`
  FROM `sys_user`;

  -- ---------- 房产：10 栋 × 4 单元 × 8 户 = 320 套 ----------
  SET v_b = 1;
  WHILE v_b <= 10 DO
    INSERT INTO `sys_property` (
      `name`, `property_type`, `parent_id`, `building_number`, `unit_number`, `room_number`, `area`, `owner_id`, `status`, `created_at`, `updated_at`
    ) VALUES (
      CONCAT(v_b, '号楼'), 'building', NULL, CAST(v_b AS CHAR), '', '', NULL, NULL, 1, NOW(), NOW()
    );
    SET v_bid = LAST_INSERT_ID();

    SET v_u = 1;
    WHILE v_u <= 4 DO
      INSERT INTO `sys_property` (
        `name`, `property_type`, `parent_id`, `building_number`, `unit_number`, `room_number`, `area`, `owner_id`, `status`, `created_at`, `updated_at`
      ) VALUES (
        CONCAT(v_b, '栋', v_u, '单元'), 'unit', v_bid, CAST(v_b AS CHAR), CAST(v_u AS CHAR), '', NULL, NULL, 1, NOW(), NOW()
      );
      SET v_uid = LAST_INSERT_ID();

      SET v_r = 1;
      WHILE v_r <= 8 DO
        SET v_owner = 7 + ((v_room_count + v_r + v_u * 3 + v_b * 5) % 40);
        INSERT INTO `sys_property` (
          `name`, `property_type`, `parent_id`, `building_number`, `unit_number`, `room_number`, `area`, `owner_id`, `status`, `created_at`, `updated_at`
        ) VALUES (
          CONCAT(v_b, '-', v_u, '-', LPAD(v_r, 2, '0')),
          'room',
          v_uid,
          CAST(v_b AS CHAR),
          CAST(v_u AS CHAR),
          LPAD(v_r, 2, '0'),
          65.00 + (v_r * 1.25) + (v_u * 0.5),
          v_owner,
          1,
          NOW(),
          NOW()
        );
        SET v_r = v_r + 1;
      END WHILE;

      SET v_u = v_u + 1;
    END WHILE;

    SET v_room_count = v_room_count + 32;
    SET v_b = v_b + 1;
  END WHILE;

  -- ---------- 收费项目（逐条插入以拿到稳定的主键）----------
  INSERT INTO `finance_charge_item` (`name`, `type`, `unit_price`, `unit`, `description`, `is_active`, `created_at`, `updated_at`)
  VALUES ('住宅物业费', 'property_fee', 2.80, '元/㎡·月', '按建筑面积计', 1, NOW(), NOW());
  SET v_ci1 = LAST_INSERT_ID();
  INSERT INTO `finance_charge_item` (`name`, `type`, `unit_price`, `unit`, `description`, `is_active`, `created_at`, `updated_at`)
  VALUES ('地下停车费', 'parking_fee', 300.00, '元/月·位', '固定车位', 1, NOW(), NOW());
  SET v_ci2 = LAST_INSERT_ID();
  INSERT INTO `finance_charge_item` (`name`, `type`, `unit_price`, `unit`, `description`, `is_active`, `created_at`, `updated_at`)
  VALUES ('代收水费', 'water_fee', 4.20, '元/吨', '代收', 1, NOW(), NOW());

  -- ---------- 账单：每套房 × 2 项目 × 3 个月（部分已缴）----------
  SELECT COUNT(*) INTO v_room_total FROM `sys_property` WHERE `property_type` = 'room';
  SET v_room_idx = 0;
  room_bill_loop: WHILE v_room_idx < v_room_total DO
    SELECT `id` INTO v_rid FROM `sys_property` WHERE `property_type` = 'room' ORDER BY `id` LIMIT 1 OFFSET v_room_idx;

    SET v_i = 1;
    WHILE v_i <= 3 DO
      INSERT INTO `finance_bill` (
        `property_id`, `charge_item_id`, `year_month`, `amount`, `status`, `due_date`, `paid_at`, `remark`, `created_at`, `updated_at`
      ) VALUES (
        v_rid,
        v_ci1,
        CONCAT('2026-0', v_i),
        220.00 + v_i * 10,
        IF(RAND() > 0.45, 'paid', 'unpaid'),
        CONCAT('2026-0', v_i, '-28'),
        IF(RAND() > 0.45, DATE_ADD(NOW(), INTERVAL -v_i DAY), NULL),
        '',
        NOW(),
        NOW()
      );

      INSERT INTO `finance_bill` (
        `property_id`, `charge_item_id`, `year_month`, `amount`, `status`, `due_date`, `paid_at`, `remark`, `created_at`, `updated_at`
      ) VALUES (
        v_rid,
        v_ci2,
        CONCAT('2026-0', v_i),
        300.00,
        IF(RAND() > 0.6, 'unpaid', 'paid'),
        CONCAT('2026-0', v_i, '-25'),
        IF(RAND() > 0.6, NULL, DATE_ADD(NOW(), INTERVAL -v_i * 2 DAY)),
        '',
        NOW(),
        NOW()
      );

      SET v_i = v_i + 1;
    END WHILE;

    SET v_room_idx = v_room_idx + 1;
  END WHILE room_bill_loop;

  -- 缴费记录（仅为已付账单补记录）
  INSERT INTO `finance_payment_record` (`bill_id`, `amount`, `payment_method`, `transaction_no`, `payment_time`, `operator_id`, `remark`)
  SELECT
    `id`,
    `amount`,
    IF(RAND() > 0.5, 'wechat', 'alipay'),
    CONCAT('MOCK-', `id`, '-', UNIX_TIMESTAMP()),
    IFNULL(`paid_at`, NOW()),
    1,
    '种子数据'
  FROM `finance_bill`
  WHERE `status` = 'paid';

  -- ---------- 报修单 120 条 ----------
  SET v_rep = 1;
  WHILE v_rep <= 120 DO
    SET v_rid = (SELECT `id` FROM `sys_property` WHERE `property_type` = 'room' ORDER BY RAND() LIMIT 1);
    SET v_owner = (SELECT `owner_id` FROM `sys_property` WHERE `id` = v_rid);
    INSERT INTO `property_repair_order` (
      `property_id`, `user_id`, `description`, `images`, `status`, `assigned_to_id`, `assigned_at`, `completed_at`, `remark`, `created_at`, `updated_at`
    ) VALUES (
      v_rid,
      v_owner,
      CONCAT('测试报修：', ELT(1 + FLOOR(RAND() * 5), '水管漏水', '电梯异响', '门禁失灵', '楼道灯不亮', '窗户密封条脱落')),
      JSON_ARRAY(),
      ELT(1 + FLOOR(RAND() * 4), 'pending', 'processing', 'completed', 'cancelled'),
      IF(RAND() > 0.15, 2 + FLOOR(RAND() * 5), NULL),
      IF(RAND() > 0.3, DATE_ADD(NOW(), INTERVAL -FLOOR(RAND() * 10) DAY), NULL),
      IF(RAND() > 0.5, DATE_ADD(NOW(), INTERVAL -FLOOR(RAND() * 3) DAY), NULL),
      IF(RAND() > 0.7, '已现场处理', ''),
      DATE_ADD(NOW(), INTERVAL -FLOOR(RAND() * 40) DAY),
      NOW()
    );
    SET v_rep = v_rep + 1;
  END WHILE;

  -- ---------- 已完成工单的反馈（每单最多一条，避免 OneToOne 冲突）----------
  INSERT INTO `property_service_feedback` (`order_id`, `rating`, `comment`, `created_at`)
  SELECT
    ro.`id`,
    3 + FLOOR(RAND() * 3),
    ELT(1 + FLOOR(RAND() * 4), '响应及时', '态度不错', '一般', '希望再快一点'),
    DATE_ADD(NOW(), INTERVAL -FLOOR(RAND() * 5) DAY)
  FROM `property_repair_order` ro
  LEFT JOIN `property_service_feedback` f ON f.`order_id` = ro.`id`
  WHERE ro.`status` = 'completed' AND f.`id` IS NULL
  ORDER BY RAND()
  LIMIT 35;

  -- ---------- 投诉建议 80 条 ----------
  SET v_i = 1;
  WHILE v_i <= 80 DO
    SET v_uid_complaint = 7 + FLOOR(RAND() * 40);
    INSERT INTO `property_complaint` (
      `user_id`, `type`, `title`, `description`, `images`, `status`, `handler_id`, `handler_remark`, `completed_at`, `created_at`, `updated_at`
    ) VALUES (
      v_uid_complaint,
      ELT(1 + FLOOR(RAND() * 5), 'service', 'environment', 'security', 'facility', 'other'),
      CONCAT('测试投诉标题-', v_i),
      CONCAT('这是一条自动生成的投诉/建议内容，编号 ', v_i, '，用于列表与统计演示。'),
      JSON_ARRAY(),
      ELT(1 + FLOOR(RAND() * 3), 'pending', 'processing', 'completed'),
      IF(RAND() > 0.5, 1, NULL),
      IF(RAND() > 0.5, '已电话回访', ''),
      IF(RAND() > 0.55, DATE_ADD(NOW(), INTERVAL -FLOOR(RAND() * 8) DAY), NULL),
      DATE_ADD(NOW(), INTERVAL -FLOOR(RAND() * 60) DAY),
      NOW()
    );
    SET v_i = v_i + 1;
  END WHILE;

  -- ---------- 公告 ----------
  INSERT INTO `operation_announcement` (
    `title`, `content`, `type`, `is_published`, `publish_time`, `is_withdrawn`, `is_archived`, `created_at`, `updated_at`
  ) VALUES
  ('关于春节期间物业服务值班的通知', '各位业主：春节期间服务中心照常值班，报修电话 400-xxx-xxxx。', 'notice', 1, NOW(), 0, 0, NOW(), NOW()),
  ('小区绿化消杀计划', '本周三上午对公共区域进行消杀，请关好门窗。', 'notice', 1, DATE_SUB(NOW(), INTERVAL 2 DAY), 0, 0, NOW(), NOW()),
  ('业主羽毛球友谊赛报名', '欢迎报名，名额有限。', 'activity', 1, DATE_SUB(NOW(), INTERVAL 5 DAY), 0, 0, NOW(), NOW()),
  ('停水紧急通知（演练）', '管道抢修演练公告，实际不停水。', 'urgent', 1, NOW(), 0, 0, NOW(), NOW()),
  ('地下车库照明改造完成', '已更换节能灯具。', 'notice', 1, DATE_SUB(NOW(), INTERVAL 10 DAY), 0, 0, NOW(), NOW()),
  ('物业费缴纳提醒', '请及时缴纳 2026 年一季度费用。', 'notice', 1, NOW(), 0, 0, NOW(), NOW()),
  ('草稿公告（未发布）', '此条不应在前台展示。', 'notice', 0, NULL, 0, 0, NOW(), NOW()),
  ('已撤回公告示例', '内容已失效。', 'notice', 1, DATE_SUB(NOW(), INTERVAL 1 DAY), 1, 0, NOW(), NOW());

  -- ---------- 系统日志 ----------
  SET v_i = 1;
  WHILE v_i <= 120 DO
    INSERT INTO `operation_system_log` (`user_id`, `action`, `detail`, `ip_address`, `created_at`)
    VALUES (
      IF(RAND() > 0.2, 1 + FLOOR(RAND() * 46), NULL),
      ELT(1 + FLOOR(RAND() * 6), 'login', 'logout', 'repair_create', 'bill_pay', 'complaint_create', 'profile_update'),
      CONCAT('种子日志 #', v_i),
      CONCAT('192.168.0.', 10 + FLOOR(RAND() * 200)),
      DATE_ADD(NOW(), INTERVAL -FLOOR(RAND() * 720) HOUR)
    );
    SET v_i = v_i + 1;
  END WHILE;

END$$

DELIMITER ;

CALL `rpms_seed_demo`();

DROP PROCEDURE IF EXISTS `rpms_seed_demo`;

SET FOREIGN_KEY_CHECKS = 1;

-- 建议执行后校验
-- SELECT COUNT(*) FROM sys_user;
-- SELECT COUNT(*) FROM sys_property WHERE property_type='room';
-- SELECT COUNT(*) FROM finance_bill;

SELECT 'RPMS 测试数据导入完成。请使用 test123456 登录 admin_demo / emp01 / owner001 等账号。' AS `message`;
