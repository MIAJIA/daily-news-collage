// 用 macOS Vision 的主体识别把照片里的前景抠出来，输出带透明背景的 PNG。
// 用法：swift cutout.swift <输入图片> <输出 PNG>
import Foundation
import Vision
import CoreImage
import AppKit

let args = CommandLine.arguments
guard args.count == 3 else {
    FileHandle.standardError.write("usage: cutout.swift <in> <out.png>\n".data(using: .utf8)!)
    exit(2)
}
let inURL = URL(fileURLWithPath: args[1])
let outURL = URL(fileURLWithPath: args[2])

guard let ciIn = CIImage(contentsOf: inURL, options: [.applyOrientationProperty: true]) else {
    FileHandle.standardError.write("cannot read image\n".data(using: .utf8)!)
    exit(1)
}
let ctx = CIContext()
guard let cg = ctx.createCGImage(ciIn, from: ciIn.extent) else { exit(1) }

let request = VNGenerateForegroundInstanceMaskRequest()
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do {
    try handler.perform([request])
    guard let obs = request.results?.first else {
        FileHandle.standardError.write("no foreground found\n".data(using: .utf8)!)
        exit(3)
    }
    let buf = try obs.generateMaskedImage(ofInstances: obs.allInstances, from: handler, croppedToInstancesExtent: true)
    let ciOut = CIImage(cvPixelBuffer: buf)
    guard let cgOut = ctx.createCGImage(ciOut, from: ciOut.extent) else { exit(1) }
    let rep = NSBitmapImageRep(cgImage: cgOut)
    guard let data = rep.representation(using: .png, properties: [:]) else { exit(1) }
    try data.write(to: outURL)
    print("ok \(cgOut.width)x\(cgOut.height) instances=\(obs.allInstances.count)")
} catch {
    FileHandle.standardError.write("error: \(error)\n".data(using: .utf8)!)
    exit(1)
}
