package sync

import (
	"crypto/sha1"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"genai-gallery-backend/internal/config"
	"genai-gallery-backend/internal/metadata"
	"genai-gallery-backend/internal/models"

	"gorm.io/gorm"
)

var (
	syncLock     sync.Mutex
	lastSyncTime time.Time
	syncCooldown = 2 * time.Second
)

func CheckSync(db *gorm.DB) {
	if time.Since(lastSyncTime) < syncCooldown {
		return
	}

	if !syncLock.TryLock() {
		return
	}
	defer syncLock.Unlock()

	if time.Since(lastSyncTime) < syncCooldown {
		return
	}

	performSync(db)
	lastSyncTime = time.Now()
}

func performSync(db *gorm.DB) {
	fmt.Println("Starting sync...")
	var images []models.Image
	if err := db.Find(&images).Error; err != nil {
		fmt.Println("Error loading images:", err)
		return
	}

	existingByHash := make(map[string]*models.Image)
	existingByPath := make(map[string]*models.Image)

	for i := range images {
		img := &images[i]
		existingByHash[img.Hash] = img
		existingByPath[img.Path] = img
	}

	err := filepath.Walk(config.ImagesDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			return nil
		}

		ext := strings.ToLower(filepath.Ext(path))
		if ext != ".png" && ext != ".jpg" && ext != ".jpeg" && ext != ".webp" && ext != ".mp4" && ext != ".mov" {
			return nil
		}

		relPath, err := filepath.Rel(config.ImagesDir, path)
		if err != nil {
			return nil
		}

		hash, err := calculateSHA1(path)
		if err != nil {
			return nil
		}

		existingImg, hashExists := existingByHash[hash]

		// Check if path occupied by stale entry
		if occupant, ok := existingByPath[relPath]; ok {
			if occupant.Hash != hash {
				db.Delete(occupant)
				if occupant.Hash != "" {
					delete(existingByHash, occupant.Hash)
				}
				delete(existingByPath, relPath)
			}
		}

		if !hashExists {
			newImg := models.Image{
				Hash:      hash,
				Path:      relPath,
				CreatedAt: info.ModTime(),
			}
			if err := db.Create(&newImg).Error; err == nil {
				extractAndSaveMetadata(db, &newImg, path)
				existingByHash[hash] = &newImg
				existingByPath[relPath] = &newImg
			}
		} else {
			// Update path if changed
			if existingImg.Path != relPath {
				existingImg.Path = relPath
				db.Save(existingImg)
				existingByPath[relPath] = existingImg
			}
			// We could check if metadata missing here
		}

		return nil
	})

	if err != nil {
		fmt.Println("Walk error:", err)
	}
	fmt.Println("Sync complete")
}

func calculateSHA1(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()

	h := sha1.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

func extractAndSaveMetadata(db *gorm.DB, img *models.Image, fullPath string) {
	if !strings.HasSuffix(strings.ToLower(fullPath), ".png") {
		// Just index clean path for non-png
		updateFTS(db, img, "")
		return
	}

	items, err := metadata.ExtractMetadata(fullPath)
	if err != nil {
		updateFTS(db, img, "")
		return
	}

	var metaRows []models.ImageMetadata
	var contentBuilder strings.Builder

	for _, item := range items {
		metaRows = append(metaRows, models.ImageMetadata{
			ImageID: img.ID,
			Key:     item.Key,
			Value:   item.Value,
		})
		contentBuilder.WriteString(item.Value)
		contentBuilder.WriteString(" ")
	}

	if len(metaRows) > 0 {
		db.Create(&metaRows)
	}

	updateFTS(db, img, contentBuilder.String())
}

func updateFTS(db *gorm.DB, img *models.Image, extraContent string) {
	db.Exec("DELETE FROM search_index WHERE image_id = ?", img.ID)

	fullContent := img.Path + " " + img.Prompt + " " + extraContent
	db.Exec("INSERT INTO search_index (image_id, content) VALUES (?, ?)", img.ID, fullContent)
}
