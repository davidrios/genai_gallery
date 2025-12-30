package database

import (
	"log"

	"genai-gallery-backend/internal/models"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

var DB *gorm.DB

func InitDB(dbPath string) {
	var err error
	DB, err = gorm.Open(sqlite.Open(dbPath), &gorm.Config{})
	if err != nil {
		log.Fatal("failed to connect database:", err)
	}

	// AutoMigrate
	err = DB.AutoMigrate(&models.Image{}, &models.ImageMetadata{})
	if err != nil {
		log.Fatal("failed to migrate database:", err)
	}

	// Create FTS5 table
	// Note: We use image_id as UNINDEXED column to reference the Image.ID (Integer)
	err = DB.Exec("CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(image_id UNINDEXED, content)").Error
	if err != nil {
		log.Fatal("failed to create fts table:", err)
	}
}

func GetDB() *gorm.DB {
	return DB
}
