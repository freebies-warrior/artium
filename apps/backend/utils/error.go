package utils

type ErrorResponse struct {
	Error struct {
		Code    string         `json:"code"`
		Message string         `json:"message"`
		Details map[string]any `json:"details"`
	} `json:"error"`
}

func NewError(code, message string, details map[string]any) ErrorResponse {
	if details == nil {
		details = map[string]any{}
	}
	var resp ErrorResponse
	resp.Error.Code = code
	resp.Error.Message = message
	resp.Error.Details = details
	return resp
}
