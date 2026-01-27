DROP TRIGGER IF EXISTS trg_items_set_updated_at ON bids;

CREATE TRIGGER trg_bids_set_updated_at
BEFORE UPDATE ON bids
FOR EACH ROW
EXECUTE FUNCTION tg_set_updated_at();
