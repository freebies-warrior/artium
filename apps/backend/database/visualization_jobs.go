package database

import (
	"context"
	"database/sql"
	"errors"
	"time"
)

type VisualizationJobDatabase struct {
	db *sql.DB
}

func NewVisualizationJobDatabase(db *sql.DB) *VisualizationJobDatabase {
	return &VisualizationJobDatabase{db: db}
}

type VisualizationJob struct {
	ID                string    `json:"id"`
	UserID            string    `json:"user_id"`
	ItemID            string    `json:"item_id"`
	ItemImageKey      string    `json:"item_image_key"`
	RoomImageKey      string    `json:"room_image_key"`
	Status            string    `json:"status"`
	ResultImageKey    *string   `json:"result_image_key,omitempty"`
	ResultDescription *string   `json:"result_description,omitempty"`
	ErrorMessage      *string   `json:"error_message,omitempty"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}

type CreateVisualizationJobArgs struct {
	UserID       string
	ItemID       string
	ItemImageKey string
	RoomImageKey string
}

func (r *VisualizationJobDatabase) CreateJob(ctx context.Context, a CreateVisualizationJobArgs) (VisualizationJob, error) {
	var job VisualizationJob

	var (
		outResultKey sql.NullString
		outDesc      sql.NullString
		outErr       sql.NullString
	)

	err := r.db.QueryRowContext(ctx, `
		INSERT INTO visualization_jobs (user_id, item_id, item_image_key, room_image_key, status)
		VALUES ($1::uuid, $2::uuid, $3, $4, 'queued')
		RETURNING
			id::text, user_id::text, item_id::text,
			item_image_key, room_image_key, status,
			result_image_key, result_description, error_message,
			created_at, updated_at
	`, a.UserID, a.ItemID, a.ItemImageKey, a.RoomImageKey).Scan(
		&job.ID, &job.UserID, &job.ItemID,
		&job.ItemImageKey, &job.RoomImageKey, &job.Status,
		&outResultKey, &outDesc, &outErr,
		&job.CreatedAt, &job.UpdatedAt,
	)
	if err != nil {
		return VisualizationJob{}, err
	}

	if outResultKey.Valid {
		job.ResultImageKey = &outResultKey.String
	}
	if outDesc.Valid {
		job.ResultDescription = &outDesc.String
	}
	if outErr.Valid {
		job.ErrorMessage = &outErr.String
	}

	return job, nil
}

func (r *VisualizationJobDatabase) GetJobByID(ctx context.Context, jobID string) (VisualizationJob, error) {
	var job VisualizationJob
	var (
		outResultKey sql.NullString
		outDesc      sql.NullString
		outErr       sql.NullString
	)

	err := r.db.QueryRowContext(ctx, `
		SELECT
			id::text, user_id::text, item_id::text,
			item_image_key, room_image_key, status,
			result_image_key, result_description, error_message,
			created_at, updated_at
		FROM visualization_jobs
		WHERE id = $1::uuid
	`, jobID).Scan(
		&job.ID, &job.UserID, &job.ItemID,
		&job.ItemImageKey, &job.RoomImageKey, &job.Status,
		&outResultKey, &outDesc, &outErr,
		&job.CreatedAt, &job.UpdatedAt,
	)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return VisualizationJob{}, ErrNotFound
		}
		return VisualizationJob{}, err
	}

	if outResultKey.Valid {
		job.ResultImageKey = &outResultKey.String
	}
	if outDesc.Valid {
		job.ResultDescription = &outDesc.String
	}
	if outErr.Valid {
		job.ErrorMessage = &outErr.String
	}

	return job, nil
}

type UpdateVisualizationJobArgs struct {
	Status            string
	ResultImageKey    *string
	ResultDescription *string
	ErrorMessage      *string
}

func (r *VisualizationJobDatabase) UpdateJobInternal(ctx context.Context, jobID string, a UpdateVisualizationJobArgs) error {
	var rk sql.NullString
	var rd sql.NullString
	var em sql.NullString

	if a.ResultImageKey != nil {
		rk = sql.NullString{String: *a.ResultImageKey, Valid: true}
	}
	if a.ResultDescription != nil {
		rd = sql.NullString{String: *a.ResultDescription, Valid: true}
	}
	if a.ErrorMessage != nil {
		em = sql.NullString{String: *a.ErrorMessage, Valid: true}
	}

	res, err := r.db.ExecContext(ctx, `
		UPDATE visualization_jobs
		SET
			status = $2,
			result_image_key = $3,
			result_description = $4,
			error_message = $5
		WHERE id = $1::uuid
	`, jobID, a.Status, rk, rd, em)
	if err != nil {
		return err
	}

	n, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if n == 0 {
		return ErrNotFound
	}
	return nil
}

func (r *VisualizationJobDatabase) ItemHasPictureKey(ctx context.Context, itemID string, pictureKey string) (bool, error) {
	var ok bool
	err := r.db.QueryRowContext(ctx, `
		SELECT EXISTS(
			SELECT 1
			FROM pictures
			WHERE item_id = $1::uuid AND key = $2
		)
	`, itemID, pictureKey).Scan(&ok)
	if err != nil {
		return false, err
	}
	return ok, nil
}
