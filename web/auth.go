package main

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/gofiber/fiber/v2"
)

var lwaHTTP = &http.Client{Timeout: 8 * time.Second}

const (
	cookieSession = "panel_session"
	cookieOAuth   = "panel_oauth"
	sessionTTL    = 30 * 24 * time.Hour
)

type sessionUser struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
	Exp   int64  `json:"exp"`
}

func publicBase() string {
	if v := os.Getenv("PUBLIC_BASE"); v != "" {
		return strings.TrimRight(v, "/")
	}
	return "http://127.0.0.1:8787"
}

func lwaClientID() string     { return os.Getenv("LWA_CLIENT_ID") }
func lwaClientSecret() string { return os.Getenv("LWA_CLIENT_SECRET") }
func sessionSecret() []byte   { return []byte(os.Getenv("SESSION_SECRET")) }

func lwaConfigured() bool {
	return lwaClientID() != "" && lwaClientSecret() != "" && len(sessionSecret()) > 0
}

func redirectURI() string {
	return publicBase() + "/auth/amazon/callback"
}

func signSession(u sessionUser) (string, error) {
	u.Exp = time.Now().Add(sessionTTL).Unix()
	raw, err := json.Marshal(u)
	if err != nil {
		return "", err
	}
	mac := hmac.New(sha256.New, sessionSecret())
	mac.Write(raw)
	sig := mac.Sum(nil)
	return base64.RawURLEncoding.EncodeToString(raw) + "." + base64.RawURLEncoding.EncodeToString(sig), nil
}

func parseSession(tok string) (sessionUser, bool) {
	var zero sessionUser
	parts := strings.Split(tok, ".")
	if len(parts) != 2 {
		return zero, false
	}
	raw, err := base64.RawURLEncoding.DecodeString(parts[0])
	if err != nil {
		return zero, false
	}
	sig, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return zero, false
	}
	mac := hmac.New(sha256.New, sessionSecret())
	mac.Write(raw)
	if !hmac.Equal(sig, mac.Sum(nil)) {
		return zero, false
	}
	if err := json.Unmarshal(raw, &zero); err != nil {
		return sessionUser{}, false
	}
	if time.Now().Unix() > zero.Exp {
		return sessionUser{}, false
	}
	if zero.ID == "" {
		return sessionUser{}, false
	}
	return zero, true
}

func currentUser(c *fiber.Ctx) (sessionUser, bool) {
	return parseSession(c.Cookies(cookieSession))
}

func requireUser(c *fiber.Ctx) error {
	if _, ok := currentUser(c); !ok {
		return c.Status(401).JSON(fiber.Map{"error": "sign in with Amazon"})
	}
	return c.Next()
}

func setCookie(c *fiber.Ctx, name, val string, maxAge int) {
	ck := &fiber.Cookie{
		Name:     name,
		Value:    val,
		Path:     "/",
		HTTPOnly: true,
		SameSite: "Lax",
		MaxAge:   maxAge,
	}
	if strings.HasPrefix(publicBase(), "https://") {
		ck.Secure = true
	}
	c.Cookie(ck)
}

func randState() (string, error) {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(b[:]), nil
}

func handleLogin(c *fiber.Ctx) error {
	if !lwaConfigured() {
		return c.Status(503).SendString("Login with Amazon is not configured yet (LWA_CLIENT_ID / LWA_CLIENT_SECRET / SESSION_SECRET).")
	}
	st, err := randState()
	if err != nil {
		return c.Status(500).SendString("could not start login")
	}
	setCookie(c, cookieOAuth, st, 600)
	u := url.URL{
		Scheme: "https",
		Host:   "www.amazon.com",
		Path:   "/ap/oa",
	}
	q := u.Query()
	q.Set("client_id", lwaClientID())
	q.Set("scope", "profile")
	q.Set("response_type", "code")
	q.Set("redirect_uri", redirectURI())
	q.Set("state", st)
	u.RawQuery = q.Encode()
	return c.Redirect(u.String(), http.StatusFound)
}

func handleLogout(c *fiber.Ctx) error {
	setCookie(c, cookieSession, "", -1)
	return c.Redirect("/", http.StatusFound)
}

type lwaToken struct {
	AccessToken string `json:"access_token"`
	Error       string `json:"error"`
	ErrorDesc   string `json:"error_description"`
}

type lwaProfile struct {
	UserID string `json:"user_id"`
	Name   string `json:"name"`
	Email  string `json:"email"`
}

func handleLWACallback(c *fiber.Ctx) error {
	if !lwaConfigured() {
		return c.Status(503).SendString("LWA is not configured")
	}
	if c.Query("error") != "" {
		return c.Status(401).SendString("Amazon login was cancelled or refused")
	}
	st := c.Query("state")
	want := c.Cookies(cookieOAuth)
	if st == "" || want == "" || !hmac.Equal([]byte(st), []byte(want)) {
		return c.Status(400).SendString("bad OAuth state")
	}
	code := c.Query("code")
	if code == "" {
		return c.Status(400).SendString("missing code")
	}
	form := url.Values{}
	form.Set("grant_type", "authorization_code")
	form.Set("code", code)
	form.Set("redirect_uri", redirectURI())
	form.Set("client_id", lwaClientID())
	form.Set("client_secret", lwaClientSecret())
	req, err := http.NewRequest(http.MethodPost, "https://api.amazon.com/auth/o2/token", strings.NewReader(form.Encode()))
	if err != nil {
		return c.Status(500).SendString(err.Error())
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	resp, err := lwaHTTP.Do(req)
	if err != nil {
		return c.Status(502).SendString("token exchange failed")
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	var tok lwaToken
	_ = json.Unmarshal(body, &tok)
	if tok.AccessToken == "" {
		return c.Status(401).SendString("Amazon token failed")
	}
	preq, err := http.NewRequest(http.MethodGet, "https://api.amazon.com/user/profile", nil)
	if err != nil {
		return c.Status(500).SendString(err.Error())
	}
	preq.Header.Set("Authorization", "Bearer "+tok.AccessToken)
	presp, err := lwaHTTP.Do(preq)
	if err != nil {
		return c.Status(502).SendString("profile failed")
	}
	defer presp.Body.Close()
	pbody, _ := io.ReadAll(io.LimitReader(presp.Body, 1<<20))
	var prof lwaProfile
	if err := json.Unmarshal(pbody, &prof); err != nil || prof.UserID == "" {
		return c.Status(401).SendString("Amazon profile failed")
	}
	u := sessionUser{
		ID:    clampString(prof.UserID, 80),
		Name:  clampString(prof.Name, 120),
		Email: clampString(prof.Email, 200),
	}
	toks, err := signSession(u)
	if err != nil {
		return c.Status(500).SendString(err.Error())
	}
	setCookie(c, cookieSession, toks, int(sessionTTL.Seconds()))
	setCookie(c, cookieOAuth, "", -1)
	if store != nil {
		_ = store.upsertProfile(c.Context(), u)
	}
	return c.Redirect("/", http.StatusFound)
}

func handleMe(c *fiber.Ctx) error {
	u, ok := currentUser(c)
	if !ok {
		return c.JSON(fiber.Map{"login": false, "lwa": lwaConfigured()})
	}
	return c.JSON(fiber.Map{
		"login": true,
		"lwa":   lwaConfigured(),
		"id":    u.ID,
		"name":  u.Name,
		"email": u.Email,
	})
}

func userPK(id string) string { return "USER#" + id }

func mustUser(c *fiber.Ctx) (sessionUser, error) {
	u, ok := currentUser(c)
	if !ok {
		return u, fmt.Errorf("unauthorized")
	}
	return u, nil
}
