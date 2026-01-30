CREATE OR REPLACE FUNCTION update_item_highest_bid_after_insert()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE items
    SET
        highest_bid_amount = NEW.price,
        highest_bidder_id  = NEW.user_id,
        highest_bid_time   = NEW.created_at
    WHERE id = NEW.item_id
        AND (
            highest_bid_amount IS NULL
            OR NEW.price > highest_bid_amount
        );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
