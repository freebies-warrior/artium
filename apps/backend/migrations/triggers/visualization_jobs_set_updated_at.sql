DROP TRIGGER IF EXISTS visualization_jobs_set_updated_at ON visualization_jobs;

CREATE TRIGGER visualization_jobs_set_updated_at
BEFORE UPDATE ON visualization_jobs
FOR EACH ROW EXECUTE FUNCTION tg_set_updated_at();