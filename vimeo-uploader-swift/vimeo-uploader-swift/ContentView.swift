//
//  ContentView.swift
//  vimeo-uploader-swift
//
//  Created by David Jeong on 12/24/22.
//

import SwiftUI

struct ContentView: View {
    
    private var gridItemLayout = [GridItem(.flexible()), GridItem(.flexible())]
    
    private let client = VimeoUploaderLambdaClient()
    private let emptyResolutions = ["N/A"]
    
    @State private var videoId: String = ""
    @State private var startTime: String = ""
    @State private var endTime: String = ""
    @State private var imageUrl: URL? = nil
    @State private var resolution: String = ""
    @State private var title: String = ""
    @State private var download: Bool = false
    
    @State private var disableVideoInputs = true
    @State private var inProgress = false
    @State private var resolutions: [String] = ["N/A"]
    
    var body: some View {
        Grid {
            GridRow {
                Text("Video ID")
                TextField("e.g. XsX3ATc3FbA", text: $videoId)
                    .onChange(of: videoId, perform: { newValue in
                        print("Video id is \(videoId)")
                        Task {
                            let videoMetadata = await client.getVideoMetadata(platform: "youtube", videoId: videoId)
                            if videoMetadata != nil {
                                if let fetchedResolutions = videoMetadata?.resolutions {
                                    resolutions = fetchedResolutions.reversed()
                                    resolution = resolutions[0]
                                }
                                disableVideoInputs = false
                            } else {
                                resetInputs()
                                disableVideoInputs = true
                            }
                        }
                    }).disabled(inProgress)
            }.padding()
            Divider()
            Group {
                GridRow {
                    Text("Video Start Time")
                    TextField("e.g. 00:45:10", text: $startTime)
                        .disabled(disableVideoInputs || inProgress)
                }.padding()
                Divider()
                GridRow {
                    Text("Video End Time")
                    TextField("e.g. 01:30:10", text: $endTime)
                        .disabled(disableVideoInputs || inProgress)
                }.padding()
            }
            Divider()
            Group {
                GridRow {
                    Text("Thumbnail Image")
                    Button("Click to select an image", action: {
                        let dialog = NSOpenPanel()
                        dialog.title = "Choose a file"
                        dialog.showsResizeIndicator = true
                        dialog.showsHiddenFiles = false
                        dialog.allowsMultipleSelection = false
                        dialog.canChooseDirectories = false
                        if (dialog.runModal() == NSApplication.ModalResponse.OK) {
                            let result = dialog.url
                            if result != nil {
                                imageUrl = result
                            } else {
                                return
                            }
                        }
                    }).disabled(disableVideoInputs || inProgress)
                }.padding()
                Divider()
                GridRow {
                    Text("Video Resolution")
                    Picker("", selection: $resolution) {
                        ForEach(resolutions, id: \.self) {
                            Text($0)
                        }
                    }
                    .pickerStyle(.segmented)
                    .disabled(disableVideoInputs || inProgress)
                }.padding()
                Divider()
                GridRow {
                    Text("Video Title")
                    TextField("e.g. BTS music video", text: $title)
                        .disabled(disableVideoInputs || inProgress)
                }.padding()
            }
            Divider()
            GridRow {
                Text("Save")
                Toggle("Download On Completion", isOn: $download).toggleStyle(.checkbox)
                    .disabled(disableVideoInputs || inProgress)
            }.padding()
            Divider()
            GridRow {
                Text("Process")
                Button("Click to start the process", action: {
                    print("Start process")
                    inProgress = true
                    Task {
                        print("Firing off task")
                        let startTimeInSec = getSeconds(time: startTime)
                        let endTimeInSec = getSeconds(time: endTime)
                        var imageContent: String?
                        var imageName: String?
                        if let url = imageUrl {
                            let imageData = try Data.init(contentsOf: url)
                            imageContent = imageData.base64EncodedString(options: .lineLength64Characters)
                            imageName = url.lastPathComponent
                        }
                        let videoProcessResult = await client.processVideo(
                            downloadPlatform: "youtube",
                            uploadPlatform: "vimeo",
                            videoId: videoId,
                            startTimeInSec: startTimeInSec,
                            endTimeInSec: endTimeInSec,
                            imageContent: imageContent,
                            imageName: imageName,
                            resolution: resolution,
                            title: title,
                            download: download)
                        if let urlString = videoProcessResult?.uploadUrl {
                            if let uploadUrl = URL(string: urlString) {
                                NSWorkspace.shared.open(uploadUrl)
                            }
                        }
                        inProgress = false
                    }
                })
                .disabled(disableVideoInputs || inProgress)
            }.padding()
        }
        .padding()
    }
    
    /**
     Calculate the number of seconds passed from time string in format hh:mm:ss
     */
    private func getSeconds(time: String) -> Int {
        let t = time.components(separatedBy: ":")
        return Int(t[0])! * 3600 + Int(t[1])! * 60 + Int(t[2])!
    }
    
    private func resetInputs() {
        resolutions = emptyResolutions
        startTime = ""
        endTime = ""
        resolution = ""
        imageUrl = nil
        title = ""
        download = false
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
