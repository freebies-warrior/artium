CREATE OR REPLACE FUNCTION update_item_highest_bid_after_insert()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE items
    SET
        highest_bid_amount = NEW.amount,
        highest_bidder_id  = NEW.user_id,
        highest_bid_at     = NEW.created_at
    WHERE id = NEW.item_id
        AND (
            highest_bid_amount IS NULL
            OR NEW.amount > highest_bid_amount
        );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
