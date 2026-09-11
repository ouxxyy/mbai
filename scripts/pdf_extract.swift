import Foundation
import PDFKit

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write(Data("usage: pdf_extract.swift <file.pdf>\n".utf8))
    exit(64)
}

let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard let document = PDFDocument(url: url) else {
    FileHandle.standardError.write(Data("PDFKit could not open the document\n".utf8))
    exit(65)
}

if let text = document.string {
    print(text, terminator: "")
}

