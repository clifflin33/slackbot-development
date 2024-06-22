def canvas():
    data = request.form
    channel_id = data.get('channel_id')

    try:
        # Step 1: Create a new canvas
        response_create = client.api_call("canvases.create")
        if response_create.get("ok"):
            canvas_id = response_create.get('canvas_id')
            client.chat_postMessage(channel=channel_id, text=f"Canvas created successfully! Canvas ID: {canvas_id}")
        else:
            error_message = f"Error creating canvas: {response_create['error']}"
            client.chat_postMessage(channel=channel_id, text=error_message)

        # Step 2: Edit the canvas that was created

        changes = [
            {
                "operation": "insert_at_start",
                "document_content":{
                    "type": "markdown",
                    "markdown": "Testing!"
                }
            }
        ]

        response_edit = client.api_call("canvases.edit", params={"canvas_id": canvas_id, "changes": changes})

        if response_edit.get("ok"):
            client.chat_postMessage(channel=channel_id, text=f"Canvas edited succesfully, Canvas ID: {canvas_id}")
        else:
            error_message = f"Error editing canvas: {response_edit['error']}"
            client.chat_postMessage(channel=channel_id, text=error_message)

    except SlackApiError as e:
        error_message = f"Slack API error: {e.response['error']}"
        client.chat_postMessage(channel=channel_id, text=error_message)

    return Response(), 200
