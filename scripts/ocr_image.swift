import Foundation
import ImageIO
import Vision

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write(Data("usage: ocr_image.swift <image.png>\n".utf8))
    exit(64)
}

let url = URL(fileURLWithPath: CommandLine.arguments[1]) as CFURL
guard
    let source = CGImageSourceCreateWithURL(url, nil),
    let image = CGImageSourceCreateImageAtIndex(source, 0, nil)
else {
    FileHandle.standardError.write(Data("could not open image\n".utf8))
    exit(65)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["zh-Hans", "en-US"]

do {
    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    try handler.perform([request])
    let observations = (request.results ?? []).sorted { left, right in
        let yDistance = abs(left.boundingBox.midY - right.boundingBox.midY)
        if yDistance > 0.015 { return left.boundingBox.midY > right.boundingBox.midY }
        return left.boundingBox.minX < right.boundingBox.minX
    }
    for observation in observations {
        if let text = observation.topCandidates(1).first?.string {
            print(text)
        }
    }
} catch {
    FileHandle.standardError.write(Data("Vision OCR failed: \(error)\n".utf8))
    exit(66)
}

