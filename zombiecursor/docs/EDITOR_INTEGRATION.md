# ZombieCursor Local AI - Editor Integration Guide

## Overview

ZombieCursor Local AI provides seamless integration with popular code editors through REST APIs and WebSocket connections. This guide covers integration with VS Code, Cursor AI, and other editors.

## Supported Editors

### 1. VS Code Integration
### 2. Cursor AI Integration
### 3. Generic Editor Integration
### 4. Custom Editor Integration

## API Endpoints

### Base URL
```
http://localhost:5051
```

### Authentication
- **API Key**: `X-API-Key` header or `api_key` query parameter
- **Token**: Bearer token authentication
- **Development**: No authentication required (default)

### Core Endpoints

#### Agent Execution
```http
POST /agent/{agent_name}/run
Content-Type: application/json

{
  "query": "Your coding question here",
  "context": "Optional project context",
  "stream": false,
  "metadata": {}
}
```

#### Streaming Response
```http
POST /agent/{agent_name}/stream
Content-Type: application/json

{
  "query": "Your coding question here",
  "context": "Optional project context",
  "stream": true,
  "metadata": {}
}
```

#### Tool Execution
```http
POST /agent/{agent_name}/tools/execute
Content-Type: application/json

{
  "tool_name": "filesystem",
  "operation": "read_file",
  "params": {
    "path": "src/main.py"
  }
}
```

#### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:5051/ws');
```

## VS Code Integration

### Method 1: Settings Configuration

Add to your VS Code `settings.json`:

```json
{
  "zombiecursor.endpoint": "http://localhost:5051",
  "zombiecursor.agent": "coder",
  "zombiecursor.apiKey": "your-api-key-here",
  "zombiecursor.autoStart": true,
  "zombiecursor.contextLines": 10,
  "zombiecursor.maxTokens": 2048
}
```

### Method 2: Extension Installation

1. Install the ZombieCursor extension from VS Code Marketplace
2. Configure the extension settings
3. Start the ZombieCursor server
4. Use the integrated chat panel

### Method 3: Custom Extension

Create a custom VS Code extension:

```typescript
// extension.ts
import * as vscode from 'vscode';
import axios from 'axios';

export function activate(context: vscode.ExtensionContext) {
    const disposable = vscode.commands.registerCommand(
        'zombiecursor.ask',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);
            
            const query = await vscode.window.showInputBox({
                prompt: 'Ask ZombieCursor:',
                placeHolder: 'Enter your question...'
            });

            if (query) {
                try {
                    const response = await axios.post(
                        'http://localhost:5051/agent/coder/run',
                        {
                            query: query,
                            context: selectedText
                        }
                    );

                    vscode.window.showInformationMessage(
                        response.data.content
                    );
                } catch (error) {
                    vscode.window.showErrorMessage(
                        `Error: ${error.message}`
                    );
                }
            }
        }
    );

    context.subscriptions.push(disposable);
}
```

### VS Code Commands

```json
{
  "contributes": {
    "commands": [
      {
        "command": "zombiecursor.ask",
        "title": "Ask ZombieCursor",
        "category": "ZombieCursor"
      },
      {
        "command": "zombiecursor.explain",
        "title": "Explain Code",
        "category": "ZombieCursor"
      },
      {
        "command": "zombiecursor.fix",
        "title": "Fix Code",
        "category": "ZombieCursor"
      }
    ],
    "keybindings": [
      {
        "command": "zombiecursor.ask",
        "key": "ctrl+shift+z",
        "mac": "cmd+shift+z"
      }
    ]
  }
}
```

## Cursor AI Integration

### Configuration

Add to Cursor AI settings:

```json
{
  "cursor.ai.endpoint": "http://localhost:5051",
  "cursor.ai.agent": "coder",
  "cursor.ai.model": "local",
  "cursor.ai.stream": true,
  "cursor.ai.context": true
}
```

### API Compatibility

ZombieCursor provides Cursor AI-compatible endpoints:

```http
POST /v1/chat/completions
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "Your question here"}
  ],
  "stream": false,
  "model": "local"
}
```

### Migration from Cursor AI

1. Stop Cursor AI service
2. Start ZombieCursor server
3. Update Cursor AI configuration
4. Test with existing workflows

## Generic Editor Integration

### REST API Client

```python
import requests
import json

class ZombieCursorClient:
    def __init__(self, base_url="http://localhost:5051", api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["X-API-Key"] = api_key

    def ask(self, query, agent="coder", context=None):
        """Ask a question to the agent."""
        payload = {
            "query": query,
            "agent_type": agent,
            "context": context
        }
        
        response = requests.post(
            f"{self.base_url}/agent/{agent}/run",
            headers=self.headers,
            json=payload
        )
        
        return response.json()

    def stream_ask(self, query, agent="coder", context=None):
        """Stream a response from the agent."""
        import websocket
        import json
        
        def on_message(ws, message):
            data = json.loads(message)
            if data.get("type") == "stream_chunk":
                print(data.get("content", ""), end="")
            elif data.get("type") == "stream_end":
                print("\n")
                ws.close()

        ws = websocket.WebSocketApp(
            f"{self.base_url.replace('http', 'ws')}/ws",
            on_message=on_message
        )
        
        payload = {
            "type": "stream_request",
            "agent": agent,
            "query": query,
            "context": context
        }
        
        ws.send(json.dumps(payload))
        ws.run_forever()

# Usage example
client = ZombieCursorClient()
response = client.ask("How do I create a Python class?")
print(response["content"])
```

### WebSocket Integration

```javascript
class ZombieCursorWS {
    constructor(url = 'ws://localhost:5051/ws') {
        this.url = url;
        this.ws = null;
        this.messageHandlers = {};
    }

    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            console.log('Connected to ZombieCursor');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const handler = this.messageHandlers[data.type];
            if (handler) {
                handler(data);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('Disconnected from ZombieCursor');
        };
    }

    ask(query, agent = 'coder', context = null) {
        const message = {
            type: 'agent_request',
            agent: agent,
            query: query,
            context: context
        };
        
        this.ws.send(JSON.stringify(message));
    }

    streamAsk(query, agent = 'coder', context = null) {
        const message = {
            type: 'stream_request',
            agent: agent,
            query: query,
            context: context
        };
        
        this.ws.send(JSON.stringify(message));
    }

    onMessage(type, handler) {
        this.messageHandlers[type] = handler;
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage example
const client = new ZombieCursorWS();
client.connect();

client.onMessage('agent_response', (data) => {
    console.log('Response:', data.content);
});

client.onMessage('stream_chunk', (data) => {
    process.stdout.write(data.content);
});

client.ask('Explain this Python function');
```

## Custom Editor Integration

### Language Server Protocol (LSP)

```typescript
import {
    createConnection,
    TextDocuments,
    ProposedFeatures,
    InitializeParams,
    TextDocumentSyncKind,
    InitializeResult
} from 'vscode-languageserver/node';
import { TextDocument } from 'vscode-languageserver-textdocument';

const connection = createConnection(ProposedFeatures.all);
const documents = new TextDocuments(TextDocument);

connection.onInitialize((params: InitializeParams) => {
    const result: InitializeResult = {
        capabilities: {
            textDocumentSync: TextDocumentSyncKind.Incremental,
            completionProvider: {
                resolveProvider: true
            }
        }
    };
    return result;
});

connection.onCompletion(async (textDocumentPosition) => {
    const doc = documents.get(textDocumentPosition.textDocument.uri);
    if (!doc) return null;

    const text = doc.getText();
    const position = textDocumentPosition.position;
    
    // Get context around cursor
    const lines = text.split('\n');
    const currentLine = lines[position.line] || '';
    const context = currentLine.trim();
    
    try {
        const response = await fetch('http://localhost:5051/agent/coder/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: `Complete this code: ${context}`,
                context: text
            })
        });
        
        const data = await response.json();
        
        return {
            items: [
                {
                    label: 'ZombieCursor Suggestion',
                    kind: 1, // Text
                    data: data.content
                }
            ]
        };
    } catch (error) {
        console.error('Error getting completion:', error);
        return null;
    }
});

documents.listen(connection);
connection.listen();
```

## Integration Examples

### Neovim Integration

```lua
-- zombiecursor.lua
local M = {}

function M.setup()
    -- Configure ZombieCursor
    vim.g.zombiecursor_endpoint = "http://localhost:5051"
    vim.g.zombiecursor_agent = "coder"
    
    -- Create commands
    vim.api.nvim_create_user_command('ZombieAsk', function(opts)
        local query = opts.args
        if query == "" then
            query = vim.fn.input("Ask ZombieCursor: ")
        end
        
        local context = vim.fn.getline('.')
        
        -- Make HTTP request
        local response = vim.fn.system(
            string.format('curl -s -X POST %s/agent/coder/run -H "Content-Type: application/json" -d \'{"query":"%s","context":"%s"}\'',
                vim.g.zombiecursor_endpoint,
                query,
                context
            )
        )
        
        -- Parse and display response
        local data = vim.json.decode(response)
        vim.notify(data.content, vim.log.levels.INFO)
    end, { nargs = "?" })
    
    -- Key mappings
    vim.api.nvim_set_keymap('n', '<leader>za', ':ZombieAsk ', { noremap = true })
    vim.api.nvim_set_keymap('v', '<leader>za', ':ZombieAsk ', { noremap = true })
end

return M
```

### Emacs Integration

```elisp
;; zombiecursor.el
(require 'json)
(require 'request)

(defvar zombiecursor-endpoint "http://localhost:5051"
  "ZombieCursor server endpoint.")

(defvar zombiecursor-agent "coder"
  "Default agent to use.")

(defun zombiecursor-ask (query &optional context)
  "Ask ZombieCursor a question."
  (interactive "sAsk ZombieCursor: ")
  
  (let* ((payload (json-encode
                   `((query . ,query)
                     (agent_type . ,zombiecursor-agent)
                     (context . ,(or context "")))))
         (url (format "%s/agent/%s/run" 
                      zombiecursor-endpoint 
                      zombiecursor-agent)))
    
    (request url
      :type "POST"
      :headers '(("Content-Type" . "application/json"))
      :data payload
      :parser (lambda () (json-read))
      :success (cl-function
                (lambda (&key data &allow-other-keys)
                  (message "ZombieCursor: %s" (plist-get data :content))))
      :error (cl-function
              (lambda (&key error-thrown &allow-other-keys)
                (message "Error: %s" (error-message-string error-thrown)))))))

(defun zombiecursor-explain-region ()
  "Explain the selected region."
  (interactive)
  (let ((context (buffer-substring (region-beginning) (region-end))))
    (zombiecursor-ask "Explain this code" context)))

(define-key global-map (kbd "C-c z a") 'zombiecursor-ask)
(define-key global-map (kbd "C-c z e") 'zombiecursor-explain-region)

(provide 'zombiecursor)
```

## Testing Integration

### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### Agent Status

```http
GET /agent/coder/info
```

Response:
```json
{
  "agent_name": "coder",
  "persona": "...",
  "capabilities": {...},
  "health": {
    "healthy": true,
    "llm": true,
    "tools": {...},
    "memory": true
  }
}
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if ZombieCursor server is running
   - Verify port configuration (default: 5051)
   - Check firewall settings

2. **Authentication Errors**
   - Verify API key configuration
   - Check authentication method
   - Ensure proper header format

3. **Slow Responses**
   - Check LLM backend health
   - Monitor system resources
   - Consider reducing context size

4. **WebSocket Issues**
   - Verify WebSocket support in editor
   - Check proxy settings
   - Ensure proper URL format (ws:// vs wss://)

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m server.main
```

### Performance Optimization

1. **Reduce Context Size**
   ```json
   {
     "max_context_files": 20,
     "max_context_size": 1500
   }
   ```

2. **Enable Caching**
   ```json
   {
     "enable_memory": true,
     "enable_streaming": true
   }
   ```

3. **Optimize LLM Settings**
   ```json
   {
     "llm_temperature": 0.3,
     "llm_max_tokens": 1024
   }
   ```

## Advanced Features

### Multi-Agent Support

```http
POST /agent/writer/run
POST /agent/retriever/run
POST /agent/explainer/run
```

### Batch Operations

```http
POST /agent/coder/batch
Content-Type: application/json

{
  "requests": [
    {"query": "What is this function?"},
    {"query": "How can I optimize this?"}
  ]
}
```

### Real-time Collaboration

```javascript
// Multiple clients can connect to the same WebSocket
// and receive real-time updates
const ws = new WebSocket('ws://localhost:5051/ws?client_id=editor1');
```

This integration guide provides comprehensive information for connecting ZombieCursor Local AI with various editors and development environments.