function generateEnv() {
    const storage = window.localStorage;
    
    // Attempt to grab session ID from storage
    // Fallback to searching common keys if specific keys aren't found
    const token = storage.getItem("_token") || "";
    const deviceId = storage.getItem("USER_HARD_WARE_INFO") || storage.getItem("device_id") || "44887752";
    const userId = storage.getItem("ANONYMOUS_REAL_USER_ID") || storage.getItem("user_id") || "";

    if (!token) {
        console.error("Could not find '_token' in localStorage. Are you logged in?");
        return;
    }

    const envContent = `MINIMAX_TOKEN=${token}
MINIMAX_USER_ID=${userId}
MINIMAX_DEVICE_ID=${deviceId}`;

    console.log("%cCredentials Extracted! Copy the lines below into a file named .env:", "color: #00ff00; font-size: 16px; font-weight: bold;");
    console.log(envContent);
}

generateEnv();