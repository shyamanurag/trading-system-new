{
  "name": "Trading System Integration",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "trading-signal",
        "responseMode": "responseNode",
        "options": {}
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "webhookId": "trading-webhook-1"
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json[\"signal_type\"]}}",
              "operation": "equals",
              "value2": "BUY"
            }
          ]
        }
      },
      "name": "Signal Router",
      "type": "n8n-nodes-base.if",
      "position": [450, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "Signal Router",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}