use `lucky`;
CREATE TABLE IF NOT EXISTS `combine_awarded_order` (
    `id` bigint(20) not null,
    `status` int not null default 0,
    `ship_status` int not null default 0,
    `buyer` bigint(20) not null,
    `is_virtual` tinyint(4) default 0,
    `goods_id` bigint(20) not null,
    `activity_id` varchar(64) not null,
    `activity_name` varchar(64) not null,
    `term_number` int not null,
    `target_amount` int not null,
    `receipt_address` text,
    `award_time` varchar(32),
    `send_time` varchar(16),
    `express` varchar(16),
    `express_num` varchar(64),
    `buy_from` varchar(32),
    `buy_price` decimal(20, 2),
    `remark` text,
    `extend` text,
    `created_at` timestamp not null default CURRENT_TIMESTAMP,
    `updated_at` timestamp not null default '0000-00-00 00:00:00',
    PRIMARY KEY `pk_id`(`id`),
    INDEX `buyer_idx` (`buyer`),
    INDEX `award_idx` (`award_time`),
    INDEX `send_idx` (`send_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DELIMITER $$
drop trigger if exists tri_order_created $$
create trigger tri_order_created after insert on `awarded_order` for each row
    begin
        declare m_target_amount integer;
        declare m_goods_id bigint;
        declare m_is_virtual tinyint;

        select goods_id, target_amount from `activity`
        where id=NEW.activity_id into m_goods_id, m_target_amount;

        set m_is_virtual = (select is_virtual from account where id=NEW.user_id);

        insert into `combine_awarded_order` values (
            NEW.order_id, NEW.status, NEW.ship_status, NEW.user_id,
            m_is_virtual, m_goods_id, NEW.activity_id,
            NEW.activity_name, NEW.term_number, m_target_amount,
            NEW.receipt_address, null, null, null, null, null, null,
            NEW.remark, NEW.extend, NEW.created_at, NEW.updated_at);
    end$$
drop trigger if exists tri_goods_updated $$
DELIMITER ;