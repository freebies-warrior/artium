DROP TRIGGER IF EXISTS trg_items_set_updated_at ON items;

CREATE TRIGGER trg_items_set_updated_at
BEFORE UPDATE ON items
FOR EACH ROW
EXECUTE FUNCTION tg_set_updated_at();
