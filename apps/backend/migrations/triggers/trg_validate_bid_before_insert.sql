DROP TRIGGER IF EXISTS trg_validate_bid_before_insert ON bids;

CREATE TRIGGER trg_validate_bid_before_insert
BEFORE INSERT ON bids
FOR EACH ROW
EXECUTE FUNCTION validate_bid_before_insert();
