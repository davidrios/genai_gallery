package metadata

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type MetadataItem struct {
	Key   string
	Value string
}

// ExtractMetadata reads ComfyUI metadata from PNG
func ExtractMetadata(filepath string) ([]MetadataItem, error) {
	file, err := os.Open(filepath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	// Check PNG signature
	var header [8]byte
	if _, err := io.ReadFull(file, header[:]); err != nil {
		return nil, err
	}
	if string(header[:]) != "\x89PNG\r\n\x1a\n" {
		// Not a PNG, just return empty (e.g. JPG)
		return nil, nil
	}

	var promptJSON string

	for {
		var length uint32
		if err := binary.Read(file, binary.BigEndian, &length); err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}

		var typeBytes [4]byte
		if _, err := io.ReadFull(file, typeBytes[:]); err != nil {
			return nil, err
		}
		chunkType := string(typeBytes[:])

		if chunkType == "tEXt" {
			data := make([]byte, length)
			if _, err := io.ReadFull(file, data); err != nil {
				return nil, err
			}
			parts := bytes.SplitN(data, []byte{0}, 2)
			if len(parts) == 2 {
				key := string(parts[0])
				// ComfyUI uses 'prompt' or 'workflow'
				if key == "prompt" {
					promptJSON = string(parts[1])
				}
			}
		} else {
			// Skip data
			if _, err := file.Seek(int64(length), io.SeekCurrent); err != nil {
				return nil, err
			}
		}

		// Skip CRC
		if _, err := file.Seek(4, io.SeekCurrent); err != nil {
			return nil, err
		}

		if promptJSON != "" {
			break
		}
	}

	if promptJSON == "" {
		return nil, nil
	}

	var data map[string]interface{}
	if err := json.Unmarshal([]byte(promptJSON), &data); err != nil {
		return nil, err
	}

	var items []MetadataItem
	for _, nodeDataRaw := range data {
		nodeData, ok := nodeDataRaw.(map[string]interface{})
		if !ok {
			continue
		}

		inputs, ok := nodeData["inputs"].(map[string]interface{})
		if !ok {
			continue
		}

		for k, v := range inputs {
			if k == "type" || k == "device" {
				continue
			}

			var valStr string
			switch val := v.(type) {
			case string:
				valStr = val
			case float64:
				if val == float64(int64(val)) {
					valStr = fmt.Sprintf("%d", int64(val))
				} else {
					valStr = fmt.Sprintf("%g", val)
				}
			case bool:
				valStr = fmt.Sprintf("%v", val)
			default:
				continue
			}

			items = append(items, MetadataItem{Key: k, Value: valStr})
		}
	}

	return items, nil
}
