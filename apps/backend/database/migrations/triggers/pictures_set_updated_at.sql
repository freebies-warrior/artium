DROP TRIGGER IF EXISTS trg_items_set_updated_at ON pictures;

CREATE TRIGGER trg_pictures_set_updated_at
BEFORE UPDATE ON pictures
FOR EACH ROW
EXECUTE FUNCTION tg_set_updated_at();
