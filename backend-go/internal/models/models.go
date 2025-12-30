package models

import (
	"time"
)

type Image struct {
	ID        uint      `gorm:"primaryKey;autoIncrement" json:"id"`
	Hash      string    `gorm:"type:varchar(255);index;unique" json:"hash"`
	Path      string    `gorm:"type:varchar(1024);uniqueIndex" json:"path"`
	Prompt    string    `gorm:"type:text" json:"prompt"`
	CreatedAt time.Time `json:"created_at"`

	MetadataItems []ImageMetadata `gorm:"foreignKey:ImageID;constraint:OnDelete:CASCADE" json:"metadata_items"`
}

type ImageMetadata struct {
	ID      uint   `gorm:"primaryKey;autoIncrement" json:"id"`
	ImageID uint   `gorm:"index" json:"image_id"`
	Key     string `gorm:"type:varchar(255);index" json:"key"`
	Value   string `gorm:"type:text;index" json:"value"`
}
