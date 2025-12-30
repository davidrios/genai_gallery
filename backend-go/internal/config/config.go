package config

import (
	"os"
	"path/filepath"
)

var (
	ImagesDir string
	DBPath    string
	Port      string
)

func InitConfig() {
	ImagesDir = os.Getenv("IMAGES_DIR")
	if ImagesDir == "" {
		// Default to relative path or a known location for dev
		// In python config:
		// IMAGES_DIR = os.getenv("IMAGES_DIR", os.path.join(os.getcwd(), "images"))
		// We'll default to "./images" assuming run from root or define absolute
		cwd, _ := os.Getwd()
		ImagesDir = filepath.Join(cwd, "images")
	}

	DBPath = os.Getenv("DB_PATH")
	if DBPath == "" {
		DBPath = "gallery.db"
	}

	Port = os.Getenv("PORT")
	if Port == "" {
		Port = "8000"
	}
}
