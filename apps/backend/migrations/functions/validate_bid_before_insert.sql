CREATE OR REPLACE FUNCTION validate_bid_before_insert()
RETURNS trigger AS $$
DECLARE
	v_item RECORD;
	v_highest bigint;
	v_min_required bigint;
BEGIN
	-- Lock the item row so concurrent bids serialize correctly
	SELECT id, seller_id, status, time_start, time_end, base_price, increment, highest_bid_amount
	INTO v_item
	FROM items
	WHERE id = NEW.item_id
	FOR UPDATE;

	IF NOT FOUND THEN
		RAISE EXCEPTION 'Item not found' USING ERRCODE = 'P0001';
	END IF;

	-- Basic auction state checks
	IF v_item.status <> 'active' THEN
		RAISE EXCEPTION 'Auction not active' USING ERRCODE = 'P0001';
	END IF;

	IF now() < v_item.time_start THEN
		RAISE EXCEPTION 'Auction has not started' USING ERRCODE = 'P0001';
	END IF;

	IF now() >= v_item.time_end THEN
		RAISE EXCEPTION 'Auction has ended' USING ERRCODE = 'P0001';
	END IF;

	-- Prevent seller from bidding on own item
	IF NEW.user_id = v_item.seller_id THEN
		RAISE EXCEPTION 'Seller cannot bid on own item' USING ERRCODE = 'P0001';
	END IF;

	-- Basic sanity
	IF NEW.price <= 0 THEN
		RAISE EXCEPTION 'Bid must be positive' USING ERRCODE = 'P0001';
	END IF;

	-- Use denormalized highest bid on items (no scan of bids needed)
	v_highest := v_item.highest_bid_amount;

	IF v_highest IS NULL THEN
		v_min_required := v_item.base_price;
	ELSE
		v_min_required := v_highest + v_item.increment;
	END IF;

	IF NEW.price < v_min_required THEN
		RAISE EXCEPTION 'Bid too low. Minimum required: %', v_min_required
	  	USING ERRCODE = 'P0001';
	END IF;

	RETURN NEW;
END;
$$ LANGUAGE plpgsql;
