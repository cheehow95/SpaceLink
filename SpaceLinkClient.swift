import SwiftUI
import WebRTC
import AVFoundation

// ============================================
// CONFIGURATION - UPDATE THESE VALUES
// ============================================

// For local network testing:
// let SERVER_URL = "http://192.168.1.100:8000"

// For internet (after setting up ngrok or similar):
// let SERVER_URL = "https://your-domain.ngrok-free.app"

let SERVER_URL = "http://192.168.1.100:8000" // REPLACE WITH YOUR PC's IP or domain

// Google STUN servers (free)
let ICE_SERVERS = [
    RTCIceServer(urlStrings: ["stun:stun.l.google.com:19302"]),
    RTCIceServer(urlStrings: ["stun:stun1.l.google.com:19302"]),
]

// ============================================
// MAIN VIEW
// ============================================

struct ContentView: View {
    @StateObject private var webRTCClient = WebRTCClient()
    @State private var aiCommand: String = ""
    @State private var activeModifiers: Set<String> = []
    
    // Dynamic Server URL
    @AppStorage("serverURL") private var serverURL: String = "http://192.168.1.100:8000"
    @State private var showingScanner = false
    
    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)
            
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("🚀 SpaceLink")
                        .font(.headline)
                        .foregroundColor(.green)
                    Spacer()
                    ConnectionStatus(state: webRTCClient.connectionState)
                }
                .padding()
                .background(Color(white: 0.1))
                
                // Video View (Always visible)
                WebRTCVideoView(videoTrack: webRTCClient.remoteVideoTrack)
                    .background(Color.black)
                    .cornerRadius(12)
                    .overlay(
                        TouchControlOverlay(webRTCClient: webRTCClient)
                    )
                    .frame(maxHeight: .infinity) // Specific layout choice
                
                // Controls Area (Bottom half)
                TabView {
                    // TAB 1: AI & Quick Actions
                    VStack(spacing: 15) {
                        // AI Command
                        HStack(spacing: 8) {
                            Image(systemName: "sparkles")
                                .foregroundColor(.purple)
                            TextField("AI Command...", text: $aiCommand)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .submitLabel(.send)
                                .onSubmit(sendAICommand)
                            
                            Button(action: sendAICommand) {
                                Image(systemName: "paperplane.fill")
                                    .padding(8)
                                    .background(Color.blue)
                                    .foregroundColor(.white)
                                    .clipShape(Circle())
                            }
                        }
                        .padding(.horizontal)
                        
                        // Quick Actions Grid
                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                            QuickActionButton(icon: "cursorarrow.click", label: "Left Click") {
                                webRTCClient.sendCommand(["type": "mouse_click", "data": ["button": "left"]])
                            }
                            QuickActionButton(icon: "cursorarrow.click.2", label: "Right Click") {
                                webRTCClient.sendCommand(["type": "mouse_click", "data": ["button": "right"]])
                            }
                             QuickActionButton(icon: "arrow.up.and.down", label: "Scroll") {
                                 // Simple scroll down for now
                                 webRTCClient.sendCommand(["type": "scroll", "data": ["amount": -200]])
                            }
                        }
                        .padding(.horizontal)
                        
                        Spacer()
                    }
                    .padding(.top)
                    .background(Color(white: 0.12))
                    .tabItem {
                        Label("Actions", systemImage: "wand.and.stars")
                    }
                    
                    // TAB 2: Keyboard & Modifiers
                    ScrollView {
                        VStack(spacing: 12) {
                            // Modifiers Row
                            HStack(spacing: 10) {
                                ModifierButton(label: "Shift", key: "shift", activeModifiers: $activeModifiers)
                                ModifierButton(label: "Ctrl", key: "ctrl", activeModifiers: $activeModifiers)
                                ModifierButton(label: "Alt", key: "alt", activeModifiers: $activeModifiers)
                                ModifierButton(label: "Win", key: "win", activeModifiers: $activeModifiers)
                            }
                            .padding(.horizontal)
                            
                            // Navigation Keys
                            HStack(spacing: 10) {
                                KeyButton(label: "Esc", key: "esc", action: sendKey)
                                KeyButton(label: "Tab", key: "tab", action: sendKey)
                                KeyButton(label: "⌫", key: "backspace", color: .red.opacity(0.8), action: sendKey)
                                KeyButton(label: "Ent", key: "enter", color: .blue, action: sendKey)
                            }
                            .padding(.horizontal)
                            
                            // Arrows
                            HStack(spacing: 15) {
                                Spacer()
                                KeyButton(label: "↑", key: "up", action: sendKey)
                                Spacer()
                            }
                            HStack(spacing: 15) {
                                KeyButton(label: "←", key: "left", action: sendKey)
                                KeyButton(label: "↓", key: "down", action: sendKey)
                                KeyButton(label: "→", key: "right", action: sendKey)
                            }
                            
                            // Hotkeys
                            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                                HotkeyButton(label: "Copy", icon: "doc.on.doc", keys: ["ctrl", "c"], client: webRTCClient)
                                HotkeyButton(label: "Paste", icon: "doc.on.clipboard", keys: ["ctrl", "v"], client: webRTCClient)
                                HotkeyButton(label: "Undo", icon: "arrow.uturn.backward", keys: ["ctrl", "z"], client: webRTCClient)
                                HotkeyButton(label: "Select All", icon: "checkmark.circle", keys: ["ctrl", "a"], client: webRTCClient)
                            }
                            .padding(.horizontal)
                        }
                        .padding(.top)
                    }
                    .background(Color(white: 0.12))
                    .tabItem {
                        Label("Keyboard", systemImage: "keyboard")
                    }
                    
                    // TAB 3: Connection
                    VStack(spacing: 20) {
                        Text("Connection Management")
                            .font(.headline)
                            .foregroundColor(.white)
                        
                        TextField("Server URL", text: $serverURL)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .padding(.horizontal)
                            .textContentType(.URL)
                            .keyboardType(.URL)
                            
                        Button(action: { showingScanner = true }) {
                            Label("Scan Server QR Code", systemImage: "qrcode.viewfinder")
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(10)
                        }
                        .padding(.horizontal)
                        
                        Button(action: { webRTCClient.connect(url: serverURL) }) {
                            Label("Connect to Server", systemImage: "link")
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.green)
                                .foregroundColor(.white)
                                .cornerRadius(10)
                        }
                        .disabled(webRTCClient.connectionState == .connected)
                        .opacity(webRTCClient.connectionState == .connected ? 0.6 : 1)
                        .padding(.horizontal)
                        
                        Button(action: { webRTCClient.disconnect() }) {
                            Label("Disconnect", systemImage: "xmark.circle")
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.red)
                                .foregroundColor(.white)
                                .cornerRadius(10)
                        }
                        .disabled(webRTCClient.connectionState != .connected)
                        .opacity(webRTCClient.connectionState != .connected ? 0.6 : 1)
                        .padding(.horizontal)
                        
                        if webRTCClient.connectionState == .connected {
                             Text("Connected to \(serverURL)")
                                .foregroundColor(.gray)
                                .font(.caption)
                        }
                        
                        Spacer()
                    }
                    .padding()
                    .background(Color(white: 0.12))
                    .tabItem {
                        Label("System", systemImage: "gear")
                    }
                    
                    // TAB 4: Features (New)
                    ScrollView {
                        VStack(spacing: 15) {
                            // Monitor Selection
                            VStack(alignment: .leading, spacing: 8) {
                                Text("🖥️ Display")
                                    .font(.headline)
                                    .foregroundColor(.green)
                                
                                HStack {
                                    Text("Monitor:")
                                        .foregroundColor(.gray)
                                    Picker("Monitor", selection: .constant(1)) {
                                        Text("Primary").tag(1)
                                        Text("All Monitors").tag(0)
                                    }
                                    .pickerStyle(SegmentedPickerStyle())
                                }
                            }
                            .padding()
                            .background(Color(white: 0.15))
                            .cornerRadius(10)
                            
                            // Clipboard Sync
                            VStack(alignment: .leading, spacing: 8) {
                                Text("📋 Clipboard")
                                    .font(.headline)
                                    .foregroundColor(.green)
                                
                                HStack(spacing: 10) {
                                    Button(action: { syncClipboardFromPC() }) {
                                        VStack {
                                            Image(systemName: "arrow.down.doc")
                                            Text("Get from PC")
                                                .font(.caption)
                                        }
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 10)
                                        .background(Color.blue.opacity(0.6))
                                        .foregroundColor(.white)
                                        .cornerRadius(8)
                                    }
                                    
                                    Button(action: { syncClipboardToPC() }) {
                                        VStack {
                                            Image(systemName: "arrow.up.doc")
                                            Text("Send to PC")
                                                .font(.caption)
                                        }
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 10)
                                        .background(Color.purple.opacity(0.6))
                                        .foregroundColor(.white)
                                        .cornerRadius(8)
                                    }
                                }
                            }
                            .padding()
                            .background(Color(white: 0.15))
                            .cornerRadius(10)
                            
                            // Recording
                            VStack(alignment: .leading, spacing: 8) {
                                Text("🎬 Recording")
                                    .font(.headline)
                                    .foregroundColor(.green)
                                
                                HStack(spacing: 10) {
                                    Button(action: { toggleRecording() }) {
                                        HStack {
                                            Image(systemName: "record.circle")
                                            Text("Record")
                                        }
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 10)
                                        .background(Color.red.opacity(0.6))
                                        .foregroundColor(.white)
                                        .cornerRadius(8)
                                    }
                                    
                                    Button(action: { stopRecording() }) {
                                        HStack {
                                            Image(systemName: "stop.circle")
                                            Text("Stop")
                                        }
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 10)
                                        .background(Color.gray.opacity(0.6))
                                        .foregroundColor(.white)
                                        .cornerRadius(8)
                                    }
                                }
                            }
                            .padding()
                            .background(Color(white: 0.15))
                            .cornerRadius(10)
                            
                            Spacer()
                        }
                        .padding()
                    }
                    .background(Color(white: 0.12))
                    .tabItem {
                        Label("Features", systemImage: "sparkles")
                    }
                }
                .frame(height: 350) // Fixed height for controls
            }
        }
        .sheet(isPresented: $showingScanner) {
            QRScannerView { code in
                // Parse JSON from QR code
                // Expected: {"type":"spacelink", "host":"http://...", "webrtc":true}
                if let data = code.data(using: .utf8),
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let host = json["host"] as? String {
                    
                    self.serverURL = host
                    self.showingScanner = false
                    
                    // Auto-connect after brief delay
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                        webRTCClient.connect(url: host)
                    }
                }
            }
        }
    }
    
    func sendAICommand() {
        guard !aiCommand.isEmpty else { return }
        webRTCClient.sendCommand(["prompt": aiCommand])
        aiCommand = ""
    }
    
    func sendKey(_ key: String) {
        if !activeModifiers.isEmpty {
            // Send as hotkey
            var params = Array(activeModifiers)
            params.append(key)
            webRTCClient.sendCommand(["type": "hotkey", "data": ["keys": params]])
            activeModifiers.removeAll() // Reset after use
        } else {
            // Send as regular key press
            webRTCClient.sendCommand(["type": "key_press", "data": ["key": key]])
        }
    }
    
    // MARK: - New Feature Functions
    
    func syncClipboardFromPC() {
        guard let url = URL(string: "\(serverURL)/clipboard") else { return }
        
        URLSession.shared.dataTask(with: url) { data, _, _ in
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let contentType = json["content_type"] as? String,
                  contentType == "text",
                  let text = json["data"] as? String else { return }
            
            DispatchQueue.main.async {
                UIPasteboard.general.string = text
            }
        }.resume()
    }
    
    func syncClipboardToPC() {
        guard let text = UIPasteboard.general.string,
              let url = URL(string: "\(serverURL)/clipboard") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let payload: [String: Any] = ["content_type": "text", "data": text]
        request.httpBody = try? JSONSerialization.data(withJSONObject: payload)
        
        URLSession.shared.dataTask(with: request).resume()
    }
    
    func toggleRecording() {
        guard let url = URL(string: "\(serverURL)/recording/start") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        URLSession.shared.dataTask(with: request).resume()
    }
    
    func stopRecording() {
        guard let url = URL(string: "\(serverURL)/recording/stop") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        URLSession.shared.dataTask(with: request).resume()
    }
}

// ============================================
// HELPER VIEWS
// ============================================

struct ModifierButton: View {
    let label: String
    let key: String
    @Binding var activeModifiers: Set<String>
    
    var isActive: Bool {
        activeModifiers.contains(key)
    }
    
    var body: some View {
        Button(action: {
            if isActive {
                activeModifiers.remove(key)
            } else {
                activeModifiers.insert(key)
            }
        }) {
            Text(label)
                .font(.system(size: 14, weight: .bold))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(isActive ? Color.yellow : Color.gray.opacity(0.3))
                .foregroundColor(isActive ? .black : .white)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.white.opacity(0.5), lineWidth: 1)
                )
        }
    }
}

struct KeyButton: View {
    let label: String
    let key: String
    var color: Color = Color.gray.opacity(0.3)
    let action: (String) -> Void
    
    var body: some View {
        Button(action: { action(key) }) {
            Text(label)
                .font(.system(size: 16, weight: .medium))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(color)
                .foregroundColor(.white)
                .cornerRadius(8)
        }
    }
}

struct HotkeyButton: View {
    let label: String
    let icon: String
    let keys: [String]
    let client: WebRTCClient
    
    var body: some View {
        Button(action: {
            client.sendCommand(["type": "hotkey", "data": ["keys": keys]])
        }) {
            HStack {
                Image(systemName: icon)
                Text(label)
            }
            .font(.caption)
            .bold()
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(Color.blue.opacity(0.6))
            .foregroundColor(.white)
            .cornerRadius(8)
        }
    }
}

// ============================================
// QR SCANNER
// ============================================

struct QRScannerView: UIViewControllerRepresentable {
    var didFindCode: (String) -> Void
    
    func makeUIViewController(context: Context) -> QRScannerViewController {
        let scanner = QRScannerViewController()
        scanner.delegate = context.coordinator
        return scanner
    }
    
    func updateUIViewController(_ uiViewController: QRScannerViewController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(didFindCode: didFindCode)
    }
    
    class Coordinator: NSObject, AVCaptureMetadataOutputObjectsDelegate {
        var didFindCode: (String) -> Void
        
        init(didFindCode: @escaping (String) -> Void) {
            self.didFindCode = didFindCode
        }
        
        func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
            if let metadataObject = metadataObjects.first as? AVMetadataMachineReadableCodeObject,
               let stringValue = metadataObject.stringValue {
                DispatchQueue.main.async {
                    self.didFindCode(stringValue)
                }
            }
        }
    }
}

class QRScannerViewController: UIViewController {
    var captureSession: AVCaptureSession!
    var previewLayer: AVCaptureVideoPreviewLayer!
    weak var delegate: AVCaptureMetadataOutputObjectsDelegate?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        view.backgroundColor = UIColor.black
        captureSession = AVCaptureSession()
        
        guard let videoCaptureDevice = AVCaptureDevice.default(for: .video) else { return }
        let videoInput: AVCaptureDeviceInput
        
        do {
            videoInput = try AVCaptureDeviceInput(device: videoCaptureDevice)
        } catch {
            return
        }
        
        if (captureSession.canAddInput(videoInput)) {
            captureSession.addInput(videoInput)
        } else {
            return
        }
        
        let metadataOutput = AVCaptureMetadataOutput()
        
        if (captureSession.canAddOutput(metadataOutput)) {
            captureSession.addOutput(metadataOutput)
            
            metadataOutput.setMetadataObjectsDelegate(delegate, queue: DispatchQueue.main)
            metadataOutput.metadataObjectTypes = [.qr]
        } else {
            return
        }
        
        previewLayer = AVCaptureVideoPreviewLayer(session: captureSession)
        previewLayer.frame = view.layer.bounds
        previewLayer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(previewLayer)
        
        DispatchQueue.global(qos: .userInitiated).async {
            self.captureSession.startRunning()
        }
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        if (captureSession?.isRunning == false) {
            DispatchQueue.global(qos: .userInitiated).async {
                self.captureSession.startRunning()
            }
        }
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        if (captureSession?.isRunning == true) {
            captureSession.stopRunning()
        }
    }
}

// ============================================
// CONNECTION STATUS
// ============================================

struct ConnectionStatus: View {
    let state: ConnectionState
    
    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(statusColor)
                .frame(width: 10, height: 10)
            Text(statusText)
                .font(.caption)
                .foregroundColor(.white)
        }
    }
    
    var statusColor: Color {
        switch state {
        case .connected: return .green
        case .connecting: return .yellow
        case .disconnected: return .red
        }
    }
    
    var statusText: String {
        switch state {
        case .connected: return "Connected"
        case .connecting: return "Connecting..."
        case .disconnected: return "Disconnected"
        }
    }
}

enum ConnectionState {
    case disconnected, connecting, connected
}

// ============================================
// WEBRTC CLIENT
// ============================================

class WebRTCClient: NSObject, ObservableObject {
    @Published var connectionState: ConnectionState = .disconnected
    @Published var remoteVideoTrack: RTCVideoTrack?
    
    private var peerConnection: RTCPeerConnection?
    private var dataChannel: RTCDataChannel?
    private var pcId: String?
    
    // Default fallback, but should come from connect(url:)
    private var currentServerURL: String = "http://192.168.1.100:8000"
    
    private lazy var factory: RTCPeerConnectionFactory = {
        RTCInitializeSSL()
        let videoEncoderFactory = RTCDefaultVideoEncoderFactory()
        let videoDecoderFactory = RTCDefaultVideoDecoderFactory()
        return RTCPeerConnectionFactory(
            encoderFactory: videoEncoderFactory,
            decoderFactory: videoDecoderFactory
        )
    }()
    
    func connect(url: String) {
        self.currentServerURL = url
        connect()
    }
    
    func connect() {
        DispatchQueue.main.async { self.connectionState = .connecting }
        
        let config = RTCConfiguration()
        config.iceServers = ICE_SERVERS
        config.sdpSemantics = .unifiedPlan
        
        let constraints = RTCMediaConstraints(
            mandatoryConstraints: nil,
            optionalConstraints: nil
        )
        
        peerConnection = factory.peerConnection(
            with: config,
            constraints: constraints,
            delegate: self
        )
        
        // Request offer from server
        requestOffer()
    }
    
    private func requestOffer() {
        // Use the dynamic URL
        guard let url = URL(string: "\(currentServerURL)/webrtc/offer") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 5 // Fast timeout for responsiveness
        
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            guard let self = self, let data = data else {
                print("Error requesting offer: \(error?.localizedDescription ?? "Unknown")")
                DispatchQueue.main.async { self?.connectionState = .disconnected }
                return
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let offer = json["offer"] as? [String: Any],
                   let sdp = offer["sdp"] as? String,
                   let type = offer["type"] as? String,
                   let pcId = json["pc_id"] as? String {
                    
                    self.pcId = pcId
                    let sessionDescription = RTCSessionDescription(type: RTCSdpType(rawValue: type == "offer" ? 0 : 1)!, sdp: sdp)
                    self.handleRemoteOffer(sessionDescription)
                }
            } catch {
                print("Error parsing offer: \(error)")
                DispatchQueue.main.async { self.connectionState = .disconnected }
            }
        }.resume()
    }
    
    private func handleRemoteOffer(_ offer: RTCSessionDescription) {
        peerConnection?.setRemoteDescription(offer) { [weak self] error in
            if let error = error {
                print("Error setting remote description: \(error)")
                return
            }
            self?.createAnswer()
        }
    }
    
    private func createAnswer() {
        let constraints = RTCMediaConstraints(
            mandatoryConstraints: ["OfferToReceiveVideo": "true"],
            optionalConstraints: nil
        )
        
        peerConnection?.answer(for: constraints) { [weak self] answer, error in
            guard let self = self, let answer = answer else {
                print("Error creating answer: \(error?.localizedDescription ?? "Unknown")")
                return
            }
            
            self.peerConnection?.setLocalDescription(answer) { error in
                if let error = error {
                    print("Error setting local description: \(error)")
                    return
                }
                
                // Wait for ICE gathering then send answer
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    self.sendAnswer()
                }
            }
        }
    }
    
    private func sendAnswer() {
        guard let localDescription = peerConnection?.localDescription,
              let pcId = pcId,
              let url = URL(string: "\(currentServerURL)/webrtc/answer") else { return }
        
        let answerPayload: [String: Any] = [
            "pc_id": pcId,
            "answer": [
                "sdp": localDescription.sdp,
                "type": localDescription.type == .answer ? "answer" : "offer"
            ]
        ]
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: answerPayload)
        
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            if let error = error {
                print("Error sending answer: \(error)")
                DispatchQueue.main.async { self?.connectionState = .disconnected }
            }
        }.resume()
    }
    
    func disconnect() {
        dataChannel?.close()
        peerConnection?.close()
        peerConnection = nil
        dataChannel = nil
        DispatchQueue.main.async {
            self.connectionState = .disconnected
            self.remoteVideoTrack = nil
        }
    }
    
    func sendCommand(_ command: [String: Any]) {
        guard let dataChannel = dataChannel,
              dataChannel.readyState == .open,
              let data = try? JSONSerialization.data(withJSONObject: command) else {
            print("Data channel not ready")
            return
        }
        
        let buffer = RTCDataBuffer(data: data, isBinary: false)
        dataChannel.sendData(buffer)
    }
}

// MARK: - RTCPeerConnectionDelegate
extension WebRTCClient: RTCPeerConnectionDelegate {
    func peerConnection(_ peerConnection: RTCPeerConnection, didChange stateChanged: RTCSignalingState) {
        print("Signaling state: \(stateChanged.rawValue)")
    }
    
    func peerConnection(_ peerConnection: RTCPeerConnection, didAdd stream: RTCMediaStream) {
        print("Stream added")
        if let videoTrack = stream.videoTracks.first {
            DispatchQueue.main.async {
                self.remoteVideoTrack = videoTrack
            }
        }
    }
    
    func peerConnection(_ peerConnection: RTCPeerConnection, didRemove stream: RTCMediaStream) {
        print("Stream removed")
    }
    
    func peerConnectionShouldNegotiate(_ peerConnection: RTCPeerConnection) {
        print("Should negotiate")
    }
    
    func peerConnection(_ peerConnection: RTCPeerConnection, didChange newState: RTCIceConnectionState) {
        print("ICE connection state: \(newState.rawValue)")
        DispatchQueue.main.async {
            switch newState {
            case .connected, .completed:
                self.connectionState = .connected
            case .disconnected, .failed, .closed:
                self.connectionState = .disconnected
            case .checking, .new:
                self.connectionState = .connecting
            @unknown default:
                break
            }
        }
    }
    
    func peerConnection(_ peerConnection: RTCPeerConnection, didChange newState: RTCIceGatheringState) {
        print("ICE gathering state: \(newState.rawValue)")
    }
    
    func peerConnection(_ peerConnection: RTCPeerConnection, didGenerate candidate: RTCIceCandidate) {
        print("ICE candidate generated")
    }
    
    func peerConnection(_ peerConnection: RTCPeerConnection, didRemove candidates: [RTCIceCandidate]) {
        print("ICE candidates removed")
    }
    
    func peerConnection(_ peerConnection: RTCPeerConnection, didOpen dataChannel: RTCDataChannel) {
        print("Data channel opened: \(dataChannel.label)")
        self.dataChannel = dataChannel
        dataChannel.delegate = self
    }
}

// MARK: - RTCDataChannelDelegate
extension WebRTCClient: RTCDataChannelDelegate {
    func dataChannelDidChangeState(_ dataChannel: RTCDataChannel) {
        print("Data channel state: \(dataChannel.readyState.rawValue)")
    }
    
    func dataChannel(_ dataChannel: RTCDataChannel, didReceiveMessageWith buffer: RTCDataBuffer) {
        if let message = String(data: buffer.data, encoding: .utf8) {
            print("Received: \(message)")
        }
    }
}

// ============================================
// VIDEO VIEW
// ============================================

struct WebRTCVideoView: UIViewRepresentable {
    let videoTrack: RTCVideoTrack?
    
    func makeUIView(context: Context) -> RTCMTLVideoView {
        let view = RTCMTLVideoView(frame: .zero)
        view.videoContentMode = .scaleAspectFit
        return view
    }
    
    func updateUIView(_ uiView: RTCMTLVideoView, context: Context) {
        if let track = videoTrack {
            track.add(uiView)
        }
    }
}

// ============================================
// TOUCH OVERLAY
// ============================================

struct TouchControlOverlay: View {
    @ObservedObject var webRTCClient: WebRTCClient
    @State private var isDragging = false
    @State private var zoomScale: CGFloat = 1.0
    
    // Haptic feedback generator
    private let impactFeedback = UIImpactFeedbackGenerator(style: .medium)
    
    var body: some View {
        GeometryReader { geo in
            Color.clear
                .contentShape(Rectangle())
                // Tap to click
                .onTapGesture { location in
                    let nx = location.x / geo.size.width
                    let ny = location.y / geo.size.height
                    
                    impactFeedback.impactOccurred()
                    
                    webRTCClient.sendCommand([
                        "type": "mouse_move",
                        "data": ["nx": nx, "ny": ny]
                    ])
                    
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
                        webRTCClient.sendCommand([
                            "type": "mouse_click",
                            "data": ["button": "left"]
                        ])
                    }
                }
                // Long press for right-click
                .onLongPressGesture(minimumDuration: 0.5) { location in
                    let nx = location.x / geo.size.width
                    let ny = location.y / geo.size.height
                    
                    // Strong haptic for right-click
                    let heavyFeedback = UIImpactFeedbackGenerator(style: .heavy)
                    heavyFeedback.impactOccurred()
                    
                    webRTCClient.sendCommand([
                        "type": "mouse_move",
                        "data": ["nx": nx, "ny": ny]
                    ])
                    
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
                        webRTCClient.sendCommand([
                            "type": "mouse_click",
                            "data": ["button": "right"]
                        ])
                    }
                }
                // Drag gesture for dragging items
                .gesture(
                    DragGesture(minimumDistance: 10)
                        .onChanged { value in
                            let nx = value.location.x / geo.size.width
                            let ny = value.location.y / geo.size.height
                            
                            if !isDragging {
                                isDragging = true
                                // Start drag - mouse down
                                webRTCClient.sendCommand([
                                    "type": "mouse_move",
                                    "data": ["nx": nx, "ny": ny]
                                ])
                                webRTCClient.sendCommand([
                                    "type": "mouse_down",
                                    "data": ["button": "left"]
                                ])
                            } else {
                                // Continue drag - just move
                                webRTCClient.sendCommand([
                                    "type": "mouse_move",
                                    "data": ["nx": nx, "ny": ny]
                                ])
                            }
                        }
                        .onEnded { value in
                            if isDragging {
                                isDragging = false
                                // End drag - mouse up
                                webRTCClient.sendCommand([
                                    "type": "mouse_up",
                                    "data": ["button": "left"]
                                ])
                            }
                        }
                )
                // Two-finger scroll gesture
                .gesture(
                    DragGesture(minimumDistance: 5)
                        .simultaneously(with: DragGesture(minimumDistance: 5))
                        .onChanged { value in
                            // Two-finger drag = scroll
                            if let translation = value.first?.translation {
                                let scrollAmount = translation.height > 0 ? -100 : 100
                                webRTCClient.sendCommand([
                                    "type": "scroll",
                                    "data": ["amount": scrollAmount]
                                ])
                            }
                        }
                )
        }
    }
}

// ============================================
// UI COMPONENTS
// ============================================

struct QuickActionButton: View {
    let icon: String
    let label: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.title2)
                    .frame(height: 24)
                Text(label)
                    .font(.caption2)
                    .lineLimit(1)
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .frame(height: 55)
            .background(Color.gray.opacity(0.3))
            .cornerRadius(10)
        }
    }
}

struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding()
            .background(LinearGradient(colors: [.green, .green.opacity(0.7)], startPoint: .topLeading, endPoint: .bottomTrailing))
            .foregroundColor(.black)
            .cornerRadius(12)
            .scaleEffect(configuration.isPressed ? 0.95 : 1)
    }
}

struct DangerButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding()
            .background(LinearGradient(colors: [.red, .red.opacity(0.7)], startPoint: .topLeading, endPoint: .bottomTrailing))
            .foregroundColor(.white)
            .cornerRadius(12)
            .scaleEffect(configuration.isPressed ? 0.95 : 1)
    }
}

// ============================================
// SETUP INSTRUCTIONS
// ============================================
/*
 To use this iOS client:
 
 1. Create a new Xcode project (iOS App, SwiftUI)
 
 2. Add WebRTC framework via Swift Package Manager:
    - https://github.com/nickhudkins/WebRTC-Mac-iOS-Versioned
    - Or use CocoaPods: pod 'GoogleWebRTC'
 
 3. Add to Info.plist:
    - NSCameraUsageDescription (not used but required)
    - NSMicrophoneUsageDescription (not used but required)
    - App Transport Security Settings > Allow Arbitrary Loads = YES (for development)
 
 4. Update SERVER_URL at the top of this file with your PC's address
 
 5. Build and run on your iPhone
 
 6. Ensure your PC is running: python main.py
 
 7. Tap "Scan Server QR Code" and scan the code from the PC's terminal or web interface (/qr)
*/
