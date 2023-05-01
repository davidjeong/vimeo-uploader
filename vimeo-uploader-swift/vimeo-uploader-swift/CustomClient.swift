//
//  CustomClient.swift
//  vimeo-uploader-swift
//
//  Created by David Jeong on 1/7/23.
//

import Foundation
import SotoLambda

struct AWSLambdaResponse: Codable {
    var statusCode: Int
    var headers: [String: String]
    var body: String?
}

class CustomClient {
    
    let client: AWSClient
    let decoder = JSONDecoder()
    
    init() {
        self.client = AWSClient(
            credentialProvider: .static(accessKeyId: "", secretAccessKey: ""),
            httpClientProvider: .createNew
        )
    }
    
    /**
     Get the video metadata from Lambda
     */
    func getVideoMetadata(videoId: String) async -> VideoMetadata? {
        let lambda = Lambda(client: self.client, region: .useast1)
        let body = [
            "queryStringParameters": [
                "platform": "youtube",
                "video_id": videoId
            ]
        ]
        do {
            let payload = try JSONSerialization.data(withJSONObject: body)
            let response = try await createInvokeLambdaTask(lambda: lambda, functionName: "get-video-metadata", payload: payload)
            if let r = response, r.statusCode == 200 {
                return try VideoMetadata(jsonString: r.body!)
            }
        } catch {
            dump(error)
        }
        return nil
    }
    
    /**
     Process the video on Lambda using specified parameteres
     */
    func processVideo(downloadPlatform: String,
                      uploadPlatform: String,
                      videoId: String,
                      startTimeInSec: Int,
                      endTimeInSec: Int,
                      imageIdentifier: String,
                      title: String,
                      download: Bool) async -> VideoProcessResult? {
        let lambda = Lambda(client: self.client, region: .useast1, timeout: TimeAmount.seconds(60 * 10))
        let body = [
            "body" : [
                "download_platform": downloadPlatform,
                "upload_platform": uploadPlatform,
                "video_id": videoId,
                "start_time_in_sec": startTimeInSec,
                "end_time_in_sec": endTimeInSec,
                "image_identifier": imageIdentifier,
                "title": title,
                "download": download
            ] as [String : Any]
        ]
        do {
            let payload = try JSONSerialization.data(withJSONObject: body)
            let response = try await createInvokeLambdaTask(lambda: lambda, functionName: "process-video", payload: payload)
            if let r = response, r.statusCode == 200 {
                return try VideoProcessResult(jsonString: r.body!)
            }
        } catch {
            dump(error)
        }
        return nil
    }
    
    private func createInvokeLambdaTask(lambda: Lambda, functionName: String, payload: Data) async throws -> AWSLambdaResponse? {
        let invocationRequest = Lambda.InvocationRequest(
            clientContext: nil,
            functionName: functionName,
            invocationType: Lambda.InvocationType.requestResponse,
            payload: .data(payload),
            qualifier: nil
        )
        let response = try await lambda.invoke(invocationRequest)
        if let jsonBody = response.payload, let data = jsonBody.asData() {
            return try decoder.decode(AWSLambdaResponse.self, from: data)
        }
        return nil
    }
}
