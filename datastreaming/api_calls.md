# Sample document
{
  "@timestamp": "2024-07-24T10:30:00Z",
  "sensor_id": "AGR-001",
  "location": {
    "lat": 42.3601,
    "lon": -71.0589
  },
  "temp_celsius": {
    "air": 25.5,
    "soil": 22.3
  },
  "humidity_percent": 45.7,
  "precipitation": {
    "rainfall_amount_mm": 0,
    "rainfall_intensity_mm_per_hour": 0
  },
  "soil": {
    "ph": 6.8,
    "nitrogen_ppm": 45.2,
    "phosphorus_ppm": 35.7,
    "potassium_ppm": 180.3
  }
}

// Retrieve information about snapshot settings
GET _snapshot

// Create a snapshot repository named 'agri_data_backup' using Google Cloud Storage (GCS)
PUT _snapshot/agri_data_backup
{
  "type": "gcs", // Specifies the repository type as Google Cloud Storage
  "settings": {
    "bucket": "u852020b59c6641a089cd815ba28b6", // GCS bucket name
    "client": "elastic-internal-95f1d8", // GCS client name
    "location": "snapshots/agri_data_backup" // Path within the bucket for snapshots
  }
}

// Create an Index Lifecycle Management (ILM) policy named 'agri_data_stream_policy'
PUT _ilm/policy/agri_data_stream_policy
{
  "policy": {
    "phases": {
      "hot": { // Configuration for the hot phase (active writes and queries)
        "actions": {
          "rollover": {
            "max_size": "50GB", // Rollover when index reaches 50GB
            "max_age": "30d" // Rollover after 30 days
          },
          "set_priority": {
            "priority": 100 // Set high priority for hot phase
          }
        }
      },
      "warm": { // Configuration for the warm phase (less frequently accessed data)
        "min_age": "30d", // Move to warm phase after 30 days
        "actions": {
          "shrink": {
            "number_of_shards": 1 // Reduce number of shards to 1
          },
          "forcemerge": {
            "max_num_segments": 1 // Merge segments to optimize storage
          },
          "set_priority": {
            "priority": 50 // Set medium priority for warm phase
          }
        }
      },
      "cold": { // Configuration for the cold phase (infrequently accessed data)
        "min_age": "180d", // Move to cold phase after 180 days
        "actions": {
          "set_priority": {
            "priority": 0 // Set low priority for cold phase
          },
          "searchable_snapshot": {
            "snapshot_repository": "agri_data_backup" // Create searchable snapshot in the specified repository
          }
        }
      },
      "delete": { // Configuration for the delete phase
        "min_age": "1825d", // Delete data after 1825 days (5 years)
        "actions": {
          "delete": {} // Delete the index
        }
      }
    }
  }
}

// Create a component template named 'agri_data_stream_comp_template'
PUT _component_template/agri_data_stream_comp_template
{
  "template": {
    "mappings": {
      "properties": {
        "@timestamp": {
          "type": "date" // Define timestamp field as date type
        },
        "sensor_id": {
          "type": "keyword", // Define sensor_id as keyword for exact matching
          "time_series_dimension": true // Mark sensor_id as a time series dimension
        },
        "location": {
          "type": "geo_point" // Define location as geo_point for geographical queries
        },
        "temp_celsius": {
          "properties": {
            "air": {
              "type": "double" // Define air temperature as double
            },
            "soil": {
              "type": "double" // Define soil temperature as double
            }
          }
        },
        "humidity_percent": {
          "type": "double" // Define humidity as double
        },
        "precipitation": {
          "properties": {
            "rainfall_amount_mm": {
              "type": "double" // Define rainfall amount as double
            },
            "rainfall_intensity_mm_per_hour": {
              "type": "double" // Define rainfall intensity as double
            }
          }
        },
        "soil": {
          "properties": {
            "ph": {
              "type": "double" // Define soil pH as double
            },
            "nitrogen_ppm": {
              "type": "double" // Define nitrogen level as double
            },
            "phosphorus_ppm": {
              "type": "double" // Define phosphorus level as double
            },
            "potassium_ppm": {
              "type": "double" // Define potassium level as double
            }
          }
        }
      }
    },
    "settings": {
      "number_of_shards": 1, // Set number of primary shards to 1
      "number_of_replicas": 1 // Set number of replica shards to 1
    }
  }
}

// Create an ingest pipeline named 'agri_data_stream_pipeline'
PUT _ingest/pipeline/agri_data_stream_pipeline
{
  "description": "Pipeline for converting temperatures from Celsius to Fahrenheit",
  "processors": [
    {
      "script": {
        "lang": "painless",
        "source": """
          ctx.temp_fahrenheit = new HashMap();
          if (ctx.temp_celsius != null) {
            if (ctx.temp_celsius.air != null) {
              ctx.temp_fahrenheit.air = Math.round((ctx.temp_celsius.air * 1.8 + 32) * 100) / 100.0;
            }
            if (ctx.temp_celsius.soil != null) {
              ctx.temp_fahrenheit.soil = Math.round((ctx.temp_celsius.soil * 1.8 + 32) * 100) / 100.0;
            }
          }
        """
        // This script converts Celsius temperatures to Fahrenheit and adds them to the document
      }
    }
  ]
}

// Create an index template named 'agri_data_stream_index_template'
PUT _index_template/agri_data_stream_index_template
{
  "index_patterns": [
    "agri_data_stream*" // Apply this template to indices starting with 'agri_data_stream'
  ],
  "composed_of": [
    "agri_data_stream_comp_template" // Use the previously defined component template
  ],
  "data_stream": {}, // This template is for a data stream
  "priority": 500, // Set template priority
  "template": {
    "aliases": {
      "agri_data_stream_alias_1": {} // Create an alias for the data stream
    },
    "settings": {
      "index.hidden":false,
      "index.default_pipeline": "agri_data_stream_pipeline", // Apply the ingest pipeline to all documents
      "index.lifecycle.name": "agri_data_stream_policy", // Apply the ILM policy
      "index.mode": "time_series", // Set index mode to time series
      "index.routing_path": [
        "sensor_id" // Use sensor_id for routing
      ],
      "index.time_series": {
        "start_time": "2024-07-20T00:00:00Z", // Set start time for the time series
        "end_time": "2099-12-31T23:59:59Z" // Set end time for the time series
      }
    }
  }
}

// Create the data stream
PUT _data_stream/agri_data_stream

// Post test documents using the bulk API
POST _bulk
{"create":{"_index":"agri_data_stream"}}
{"@timestamp":"2024-07-24T10:30:00Z","sensor_id":"AGR-001","location":{"lat":42.3601,"lon":-71.0589},"temp_celsius":{"air":25.5,"soil":22.3},"humidity_percent":45.7,"precipitation":{"rainfall_amount_mm":0,"rainfall_intensity_mm_per_hour":0},"soil":{"ph":6.8,"nitrogen_ppm":45.2,"phosphorus_ppm":35.7,"potassium_ppm":180.3}}
{"create":{"_index":"agri_data_stream"}}
{"@timestamp":"2024-07-25T14:15:00Z","sensor_id":"AGR-002","location":{"lat":42.3505,"lon":-71.1054},"temp_celsius":{"air":18.2,"soil":19.5},"humidity_percent":82.3,"precipitation":{"rainfall_amount_mm":15.7,"rainfall_intensity_mm_per_hour":8.2},"soil":{"ph":7.1,"nitrogen_ppm":52.8,"phosphorus_ppm":38.1,"potassium_ppm":195.6}}
{"create":{"_index":"agri_data_stream"}}
{"@timestamp":"2024-07-26T12:00:00Z","sensor_id":"AGR-003","location":{"lat":42.3314,"lon":-71.1212},"temp_celsius":{"air":32.8,"soil":28.7},"humidity_percent":30.5,"precipitation":{"rainfall_amount_mm":0,"rainfall_intensity_mm_per_hour":0},"soil":{"ph":6.5,"nitrogen_ppm":40.1,"phosphorus_ppm":33.9,"potassium_ppm":170.2}}
{"create":{"_index":"agri_data_stream"}}
{"@timestamp":"2024-07-27T08:45:00Z","sensor_id":"AGR-001","location":{"lat":42.3601,"lon":-71.0589},"temp_celsius":{"air":27.3,"soil":23.8},"humidity_percent":55.2,"precipitation":{"rainfall_amount_mm":2.3,"rainfall_intensity_mm_per_hour":1.5},"soil":{"ph":6.9,"nitrogen_ppm":46.5,"phosphorus_ppm":36.2,"potassium_ppm":182.1}}
{"create":{"_index":"agri_data_stream"}}
{"@timestamp":"2024-07-28T16:30:00Z","sensor_id":"AGR-002","location":{"lat":42.3505,"lon":-71.1054},"temp_celsius":{"air":22.1,"soil":21.7},"humidity_percent":68.9,"precipitation":{"rainfall_amount_mm":5.8,"rainfall_intensity_mm_per_hour":3.2},"soil":{"ph":7.2,"nitrogen_ppm":54.1,"phosphorus_ppm":39.3,"potassium_ppm":198.4}}
{"create":{"_index":"agri_data_stream"}}
{"@timestamp":"2024-07-29T11:20:00Z","sensor_id":"AGR-003","location":{"lat":42.3314,"lon":-71.1212},"temp_celsius":{"air":29.5,"soil":26.9},"humidity_percent":42.3,"precipitation":{"rainfall_amount_mm":0,"rainfall_intensity_mm_per_hour":0},"soil":{"ph":6.6,"nitrogen_ppm":41.8,"phosphorus_ppm":34.7,"potassium_ppm":173.5}}
{"create":{"_index":"agri_data_stream"}}
{"@timestamp":"2024-07-30T09:00:00Z","sensor_id":"AGR-001","location":{"lat":42.3601,"lon":-71.0589},"temp_celsius":{"air":26.8,"soil":23.1},"humidity_percent":50.5,"precipitation":{"rainfall_amount_mm":1.2,"rainfall_intensity_mm_per_hour":0.8},"soil":{"ph":7.0,"nitrogen_ppm":47.3,"phosphorus_ppm":36.8,"potassium_ppm":184.7}}
{"create":{"_index":"agri_data_stream"}}
{"@timestamp":"2024-07-31T13:45:00Z","sensor_id":"AGR-002","location":{"lat":42.3505,"lon":-71.1054},"temp_celsius":{"air":24.7,"soil":22.9},"humidity_percent":62.1,"precipitation":{"rainfall_amount_mm":3.5,"rainfall_intensity_mm_per_hour":2.1},"soil":{"ph":7.3,"nitrogen_ppm":55.6,"phosphorus_ppm":40.2,"potassium_ppm":201.8}}
{"create":{"_index":"agri_data_stream"}}
{"@timestamp":"2024-08-01T10:10:00Z","sensor_id":"AGR-003","location":{"lat":42.3314,"lon":-71.1212},"temp_celsius":{"air":31.2,"soil":27.8},"humidity_percent":38.7,"precipitation":{"rainfall_amount_mm":0,"rainfall_intensity_mm_per_hour":0},"soil":{"ph":6.7,"nitrogen_ppm":43.2,"phosphorus_ppm":35.5,"potassium_ppm":176.9}}
{"create":{"_index":"agri_data_stream"}}
{"@timestamp":"2024-08-02T15:30:00Z","sensor_id":"AGR-001","location":{"lat":42.3601,"lon":-71.0589},"temp_celsius":{"air":28.9,"soil":24.6},"humidity_percent":48.3,"precipitation":{"rainfall_amount_mm":0.5,"rainfall_intensity_mm_per_hour":0.3},"soil":{"ph":7.1,"nitrogen_ppm":48.7,"phosphorus_ppm":37.4,"potassium_ppm":187.2}}


// Search the data stream
GET agri_data_stream/_search

// Trigger a snapshot of the data stream
PUT _snapshot/agri_data_backup/agri_data_backup_0
{
  "indices": "agri_data_stream",
  "ignore_unavailable": true,
  "include_global_state": false
}

// Create a Snapshot Lifecycle Management (SLM) policy
PUT _slm/policy/agri_data_backup_policy
{
  "schedule": "0 30 1 * * ?", // Run daily at 1:30 AM
  "name": "<agri_data_backup-{now/d}>", // Name format for snapshots
  "repository": "agri_data_backup", // Repository to store snapshots
  "config": {
    "indices": ["agri_data_stream"], // Indices to snapshot
    "ignore_unavailable": true,
    "include_global_state": false
  },
  "retention": {
    "expire_after": "30d", // Keep snapshots for 30 days
    "min_count": 5, // Always keep at least 5 snapshots
    "max_count": 50 // Never keep more than 50 snapshots
  }
}
// Execute the SLM policy immediately
POST _slm/policy/agri_data_backup_policy/_execute

// Create a transform for weekly summary
PUT _transform/agri_data_stream_weekly_summary
{
  "source": {
    "index": "agri_data_stream" // Source index for the transform
  },
  "pivot": {
    "group_by": {
      "sensor_id": {
        "terms": {
          "field": "sensor_id" // Group by sensor ID
        }
      },
      "date":{
        "date_histogram": {
          "field": "@timestamp",
          "calendar_interval": "1w" // Group by week
        }
      }
    },
    "aggregations": {
      "avg_air_temp_celsius": {
        "avg": {
          "field": "temp_celsius.air" // Calculate average air temperature
        }
      },
      "total_rainfall":{
        "sum": {
          "field": "precipitation.rainfall_amount_mm" // Calculate total rainfall
        }
      }
    }
  },
  "dest": {
    "index": "agri_data_weekly_summary" // Destination index for the transform results
  }
}
// Start the transform
POST _transform/agri_data_stream_weekly_summary/_start
// Check transform status
GET _transform/agri_data_stream_weekly_summary/_stats
// Search the weekly summary index
GET agri_data_weekly_summary/_search

// Clean up operations (delete data stream, indices, templates, policies, etc.)
DELETE _data_stream/agri_data_stream
DELETE .ds-agri_data_stream*
DELETE agri_data_stream*
DELETE _index_template/agri_data_stream*
DELETE _component_template/agri_data_stream*
DELETE _ilm/policy/agri_data_stream_policy
DELETE */_alias/agri_data_stream_alias_1
DELETE _snapshot/agri_data_backup
DELETE _ingest/pipeline/agri_data_stream_pipeline

// Retrieve settings for the data stream
GET agri_data_stream/_settings

// Extremely comprehensive search query

GET agri_data_stream/_search
{
  "size": 20,
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-30d",
              "lte": "now"
            }
          }
        },
        {
          "geo_bounding_box": {
            "location": {
              "top_left": {
                "lat": 43.0,
                "lon": -72.0
              },
              "bottom_right": {
                "lat": 42.0,
                "lon": -71.0
              }
            }
          }
        }
      ],
      "should": [
        {
          "match_phrase": {
            "sensor_id": "AGR-001"
          }
        },
        {
          "range": {
            "temp_celsius.air": {
              "gte": 25,
              "lte": 30
            }
          }
        }
      ],
      "must_not": [
        {
          "term": {
            "precipitation.rainfall_amount_mm": 0
          }
        }
      ],
      "filter": [
        {
          "range": {
            "soil.ph": {
              "gte": 6.5,
              "lte": 7.5
            }
          }
        }
      ]
    }
  },
  "sort": [
    {
      "@timestamp": {
        "order": "desc"
      }
    },
    {
      "_geo_distance": {
        "location": {
          "lat": 42.3601,
          "lon": -71.0589
        },
        "order": "asc",
        "unit": "km"
      }
    }
  ],
  "aggs": {
    "sensor_stats": {
      "terms": {
        "field": "sensor_id",
        "size": 10
      },
      "aggs": {
        "avg_temp": {
          "avg": {
            "field": "temp_celsius.air"
          }
        },
        "max_humidity": {
          "max": {
            "field": "humidity_percent"
          }
        },
        "total_rainfall": {
          "sum": {
            "field": "precipitation.rainfall_amount_mm"
          }
        },
        "temp_percentiles": {
          "percentiles": {
            "field": "temp_celsius.air",
            "percents": [25, 50, 75, 95]
          }
        },
        "monthly_rainfall": {
          "date_histogram": {
            "field": "@timestamp",
            "calendar_interval": "month"
          },
          "aggs": {
            "total_rain": {
              "sum": {
                "field": "precipitation.rainfall_amount_mm"
              }
            }
          }
        }
      }
    },
    "avg_soil_nutrients": {
      "avg": {
        "fields": ["soil.nitrogen_ppm", "soil.phosphorus_ppm", "soil.potassium_ppm"]
      }
    },
    "temp_soil_correlation": {
      "correlation": {
        "variables": [
          {
            "field": "temp_celsius.air"
          },
          {
            "field": "temp_celsius.soil"
          }
        ]
      }
    }
  },
  "highlight": {
    "fields": {
      "sensor_id": {}
    }
  },
  "script_fields": {
    "temp_fahrenheit": {
      "script": {
        "source": "params._source.temp_celsius.air * 1.8 + 32"
      }
    }
  },
  "runtime_mappings": {
    "is_rainy": {
      "type": "boolean",
      "script": {
        "source": "emit(doc['precipitation.rainfall_amount_mm'].value > 0)"
      }
    }
  },
  "docvalue_fields": [
    "temp_celsius.air",
    "temp_celsius.soil",
    "humidity_percent"
  ],
  "collapse": {
    "field": "sensor_id",
    "inner_hits": {
      "name": "latest_reading",
      "size": 1,
      "sort": [{"@timestamp": "desc"}]
    }
  },
  "post_filter": {
    "range": {
      "soil.nitrogen_ppm": {
        "gte": 40
      }
    }
  }
}