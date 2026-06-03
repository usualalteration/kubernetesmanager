import base64
import json
import uuid
from datetime import datetime

def main(args, ctx=None):
    file_data = args.get("file_data")
    file_name = args.get("file_name")
    
    print(f"DEBUG: file_data type = {type(file_data)}")
    print(f"DEBUG: file_data length = {len(str(file_data)) if file_data else 0}")
    print(f"DEBUG: file_data first 100 chars = {str(file_data)[:100] if file_data else 'None'}")
    
    if not file_data:
        return {"error": "No file data provided"}
    
    # Decode base64 file data
    try:
        # file_data comes as string from JSON
        file_content = base64.b64decode(file_data)
        file_content_str = file_content.decode('utf-8')
        print(f"DEBUG: Successfully decoded file, length: {len(file_content_str)}")
        print(f"DEBUG: First 100 chars: {file_content_str[:100]}")
    except Exception as e:
        print(f"DEBUG: Decoding error: {str(e)}")
        return {"error": f"Failed to decode file: {str(e)}"}
    
    # Validate YAML structure
    try:
        import yaml
        config = yaml.safe_load(file_content_str)
        
        # Check if it's a valid kubeconfig
        if not config or 'apiVersion' not in config:
            return {"error": "Invalid kube-config file. No configuration found.", "valid": False}
        
        # Check for required kubeconfig fields
        if 'clusters' not in config or 'users' not in config or 'contexts' not in config:
            return {
                "error": "Invalid kube-config file. Missing required sections.", 
                "valid": False,
                "config": config
            }
        
        # Save to S3 for persistence
        if ctx and ctx.S3_CLIENT:
            try:
                unique_id = f"kubeconfigs/{uuid.uuid4()}/{file_name}"
                ctx.S3_CLIENT.put_object(
                    Bucket=ctx.S3_DATA,
                    Key=unique_id,
                    Body=file_content,
                    Metadata={
                        'filename': file_name,
                        'uploaded_at': datetime.utcnow().isoformat(),
                        'clusters': str(len(config.get('clusters', []))),
                        'users': str(len(config.get('users', [])))
                    }
                )
                return {
                    "success": True,
                    "message": "Kubeconfig saved successfully",
                    "valid": True,
                    "filename": file_name,
                    "storage_key": unique_id,
                    "config": config,
                    "clusters": len(config.get('clusters', [])),
                    "users": len(config.get('users', [])),
                    "contexts": len(config.get('contexts', []))
                }
            except Exception as e:
                return {
                    "success": True,
                    "message": "Kubeconfig validated but save failed",
                    "valid": True,
                    "filename": file_name,
                    "config": config,
                    "clusters": len(config.get('clusters', [])),
                    "users": len(config.get('users', [])),
                    "contexts": len(config.get('contexts', [])),
                    "save_error": str(e)
                }
        
        return {
            "success": True,
            "message": "Kubeconfig validated successfully",
            "valid": True,
            "filename": file_name,
            "config": config,
            "clusters": len(config.get('clusters', [])),
            "users": len(config.get('users', [])),
            "contexts": len(config.get('contexts', []))
        }
    except ImportError:
        # Fallback: basic validation without YAML parsing
        if file_content_str.strip().startswith('apiVersion:') and 'clusters:' in file_content_str:
            return {
                "success": True,
                "message": "Kubeconfig appears valid",
                "valid": True,
                "filename": file_name
            }
        return {"error": "Invalid kube-config file format", "valid": False}
