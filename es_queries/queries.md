
GET blogs_authorship_proc/_search
{
  "size": 0,
  "runtime_mappings": {
    "age_category": {
      "type": "keyword",
      "script": {
        "source": """
        def age = doc['author.age'].size() == 0 ? null : doc['author.age'].value;
        if (age < 0 || age == null) emit('unknown');
        else if (age < 20) emit('teen');
        else if (age < 35) emit('young adult');
        else if (age < 60) emit('adult');
        else emit('senior');
        """
      }
    },
    "content_length": {
      "type": "long",
      "script": {
        "source": """
      def content = params._source.content;
      if (content != null) {
        emit(content.length());
      } else {
        emit(0);
      }
      """
      }
    }
  },
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "author.gender": "female"
          }
        },
        {
          "range": {
            "@timestamp": {
              "gte": "2004-01-31||-1y"
            }
          }
        }
      ]
    }
  },
  "aggs": {
    "by_age_category": {
      "terms": {
        "field": "age_category"
      },
      "aggs": {
        "by_month": {
          "terms": {
            "script": {
              "source": """
                doc['@timestamp'].value.month.getDisplayName(TextStyle.FULL, Locale.ENGLISH)
                """
            }
          },
          "aggs": {
            "unique": {
              "cardinality": {
                "field": "uid"
              }
            },
            "average_age": {
              "avg": {
                "field": "author.age"
              }
            },
            "content_length_ranges": {
              "range": {
                "field": "content_length",
                "ranges": [
                  {
                    "to": 50
                  },
                  {
                    "from": 50,
                    "to": 100
                  }
                ]
              }
            }
          }
        }
      }
    }
  }
}
  