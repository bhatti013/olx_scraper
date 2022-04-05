#------------------------------TABLE DEFINATION------------------------
Create table tablets(
	id bigint(20) NOT NULL AUTO_INCREMENT,
	title VARCHAR (512),
	description text,
	listing_id VARCHAR (255),
	price VARCHAR(255),
	product_condition VARCHAR(255),
	product_type VARCHAR(255),
	seller_name VARCHAR(255),
	is_featured BOOLEAN,
	listing_url  VARCHAR(255),
	listing_date Date,
	created_at      DATETIME           DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (id)
)DEFAULT CHARSET = `utf8mb4`
  COLLATE = utf8mb4_unicode_520_ci;
