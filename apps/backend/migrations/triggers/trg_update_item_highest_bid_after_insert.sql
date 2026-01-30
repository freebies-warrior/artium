DROP TRIGGER IF EXISTS trg_update_item_highest_bid_after_insert ON bids;

CREATE TRIGGER trg_update_item_highest_bid_after_insert
AFTER INSERT ON bids
FOR EACH ROW
EXECUTE FUNCTION update_item_highest_bid_after_insert();
