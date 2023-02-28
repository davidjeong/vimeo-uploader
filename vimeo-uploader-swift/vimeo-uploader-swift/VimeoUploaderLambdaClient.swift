//
//  VimeoUploaderLambdaClient.swift
//  vimeo-uploader-swift
//
//  Created by David Jeong on 1/7/23.
//

import Foundation
import AWSLambda

/**
 Struct used for video metadata response from Lambda
 */
struct VideoMetadata: Codable {
    var videoId: String?
    var title: String?
    var author: String?
    var lengthInSec: Int?
    var publishDate: String?
    var resolutions: [String]?
}

/**
 Struct used for video process result response from Lambda
 */
struct VideoProcessResult: Codable {
    var uploadUrl: String?
    var downloadUrl: String?
}

/**
 Generic Lambda response struct
 */
struct LambdaResponse: Codable {
    var statusCode: Int?
    var body: String?
}

class VimeoUploaderLambdaClient {
    
    let lambdaClient: LambdaClient
    
    init() {
        do {
            // Try creating lambda client. If this is not possible the application needs to quit.
            self.lambdaClient = try LambdaClient(region: "us-east-1")
        } catch {
            dump(error, name: "init-error")
            exit(1)
        }
    }
    
    /**
     Get the video metadata from Lambda
     */
    func getVideoMetadata(platform: String, videoId: String) async -> VideoMetadata? {
        let functionName = "get-video-metadata"
        let requestBody = ["queryStringParameters": [
            "platform": platform,
            "video_id": videoId
        ]]
        do {
            let payload = try JSONSerialization.data(withJSONObject: requestBody)
            let response = await invokeLambdaFunction(functionName: functionName, payload: payload)
            if let dict = response {
                return try JSONDecoder().decode(VideoMetadata.self, from: JSONSerialization.data(withJSONObject: dict))
            }
        } catch {
            dump(error, name: "get-video-metadata-error")
        }
        return nil
    }
    
    /**
     Process the video on Lambda using specified parameteres
     */
    func processVideo(downloadPlatform: String, uploadPlatform: String, videoId: String, startTimeInSec: Int, endTimeInSec: Int, imageContent: String?, imageName: String?, resolution: String, title: String, download: Bool) async -> VideoProcessResult? {
        let functionName = "process-video"
        let requestBody = ["body" : [
            "download_platform": downloadPlatform,
            "upload_platform": uploadPlatform,
            "video_id": videoId,
            "start_time_in_sec": startTimeInSec,
            "end_time_in_sec": endTimeInSec,
            "image_content": imageContent!,
            "image_name": imageName!,
            "resolution": resolution,
            "title": title,
            "download": download
        ]]
        do {
            let payload = try JSONSerialization.data(withJSONObject: requestBody)
            let response = await invokeLambdaFunction(functionName: functionName, payload: payload)
            if let dict = response {
                return try JSONDecoder().decode(VideoProcessResult.self, from: JSONSerialization.data(withJSONObject: dict))
            }
        } catch {
            dump(error, name: "process-video-error")
        }
        return nil
    }
    
    /**
     Invoke the Lambda function using function name and payload
     */
    private func invokeLambdaFunction(functionName: String, payload: Data) async -> [String: Any]? {
        let invokeTask = Task {
            let inputObject = InvokeInput(clientContext: nil, functionName: functionName, invocationType: LambdaClientTypes.InvocationType.requestresponse, logType: LambdaClientTypes.LogType.none, payload: payload, qualifier: nil)
            let response = try await lambdaClient.invoke(input: inputObject)
            if let payload = response.payload {
                return try JSONDecoder().decode(LambdaResponse.self, from: payload)
            } else {
                return LambdaResponse(statusCode: 500, body: nil)
            }
        }
        
        do {
            let result = try await invokeTask.value
            if let body = result.body {
                let dataStringData = Data(body.utf8)
                return try JSONSerialization.jsonObject(with: dataStringData) as? [String: Any]
            }
        } catch {
            dump(error, name: "invoke-lambda-function-error")
        }
        return nil
    }
}
