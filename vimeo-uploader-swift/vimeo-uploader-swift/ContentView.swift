//
//  ContentView.swift
//  vimeo-uploader-swift
//
//  Created by David Jeong on 12/24/22.
//

import SwiftUI

struct ContentView: View {

    private var gridItemLayout = [GridItem(.flexible()), GridItem(.flexible())]
    
    
    @State private var videoId: String = ""
    @State private var startTime: String = ""
    @State private var endTime: String = ""
    @State private var resolution = ""
    @State private var title = ""
    @State private var download = false
    
    let sampleResolutions = ["240p", "360p", "480p", "640p", "720p", "1080p"].reversed()
    
    var body: some View {
        Grid {
            GridRow {
                Text("Video ID")
                TextField("e.g. XsX3ATc3FbA", text: $videoId).onChange(of: videoId, perform: { newValue in
                    // Call Lambda here
                    print("Video id is \(videoId)")
                })
            }.padding()
            Divider()
            Group {
                GridRow {
                    Text("Video Start Time")
                    TextField("e.g. 00:45:10", text: $startTime)
                }.padding()
                Divider()
                GridRow {
                    Text("Video End Time")
                    TextField("e.g. 01:30:10", text: $endTime)
                }.padding()
            }
            Divider()
            Group {
                GridRow {
                    Text("Video Resolution")
                    Picker("", selection: $resolution) {
                        ForEach(sampleResolutions, id: \.self) {
                            Text($0)
                        }
                    }.pickerStyle(.segmented)
                }.padding()
                Divider()
                GridRow {
                    Text("Video Title")
                    TextField("e.g. BTS music video", text: $title)
                }.padding()
            }
            Divider()
            GridRow {
                Text("Save")
                Toggle("Download On Completion", isOn: $download).toggleStyle(.checkbox)
            }.padding()
            Divider()
            GridRow {
                Text("Process")
                Button("Click to start the process", action: {
                    print("Start process")
                })
            }.padding()
        }
        .padding()
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
