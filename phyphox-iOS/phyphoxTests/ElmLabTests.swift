//
//  ElmLabTests.swift
//  phyphoxTests
//
//  Elm Lab: the home screen golden, the Azerbaijani strings and the first-launch language rule.
//

import XCTest
import SnapshotTesting
@testable import phyphox

final class ElmLabTests: XCTestCase {
    ///Next to the view goldens, so the test workflow's re-rendered goldens include it
    private var snapshotDirectory: String {
        return DocsCorpus.repositoryRoot
            .appendingPathComponent("phyphox-iOS/phyphoxTests/Snapshots/views/elmlab-home", isDirectory: true)
            .path
    }

    //All cards, whatever this simulator's sensors: the golden pins the layout, not the device
    func testHomeScreenSnapshot() {
        for (name, width) in [("phone", CGFloat(390)), ("tablet", CGFloat(834))] {
            let home = ElmLabHomeView(sections: ElmLab.sections)
            home.frame = CGRect(x: 0, y: 0, width: width, height: 10000)
            home.layoutIfNeeded()
            let size = CGSize(width: width, height: home.contentSize.height)
            home.frame = CGRect(origin: .zero, size: size)
            home.layoutIfNeeded()

            let failure = verifySnapshot(
                of: home,
                as: .image(size: size, traits: UITraitCollection(displayScale: 2)),
                named: name,
                snapshotDirectory: snapshotDirectory,
                testName: "home")
            if let failure = failure {
                XCTFail("elmlab-home/\(name): \(failure)")
            }
        }
    }

    func testEveryCardHasItsPictureAndTexts() {
        for section in ElmLab.sections {
            XCTAssertNotEqual(localize(section.heading), section.heading, "no text for \(section.heading)")
            for card in section.cards {
                XCTAssertNotNil(UIImage(named: card.image), "no picture \(card.image)")
                XCTAssertNotEqual(localize(card.title), card.title, "no text for \(card.title)")
                XCTAssertNotEqual(localize(card.subtitle), card.subtitle, "no text for \(card.subtitle)")
            }
        }
    }

    func testAzerbaijaniLoads() throws {
        let path = try XCTUnwrap(Bundle.main.path(forResource: "az", ofType: "lproj"), "az.lproj is not in the app")
        let az = try XCTUnwrap(Bundle(path: path))
        XCTAssertEqual(az.localizedString(forKey: "cancel", value: nil, table: nil), "Ləğv et")
        XCTAssertEqual(az.localizedString(forKey: "elmlabSensorHeading", value: nil, table: nil), "Sensorlar")
    }

    func testAzerbaijaniIsTheDefaultOnlyOnAFreshLaunch() {
        let plain = ["/app"]
        XCTAssertTrue(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: nil, arguments: plain, environment: [:]))
        //Once only, so a later change in the system settings sticks
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: true, appLanguages: nil, arguments: plain, environment: [:]))
        //The user already picked a language for the app
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: ["ru"], arguments: plain, environment: [:]))
        //Tests and automation pin their own language
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: nil, arguments: plain, environment: ["XCTestConfigurationFilePath": "x"]))
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: nil, arguments: plain + ["-AppleLanguages", "(en)"], environment: [:]))
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: nil, arguments: plain + ["-phyphoxUrl", "phyphox://x"], environment: [:]))
        XCTAssertFalse(ElmLab.shouldSetDefaultLanguage(alreadySet: false, appLanguages: nil, arguments: plain + ["screenshot"], environment: [:]))
    }
}

///Elm Lab has no depth sensor support: App Review rejected build 15 under guidelines 2.5.1 and
///4.2.1 for the depth sensor code phyphox carries for its LiDAR experiments, which no Elm Lab
///experiment uses. The code is gone, so files with a depth input or a depth-gui view are refused, and the
///release drops the bundled ones (tools/elmlab/strip_phyphox_org.py).
enum ElmLabNoDepth {
    static func uses(_ url: URL) -> Bool {
        guard let text = try? String(contentsOf: url, encoding: .utf8) else { return false }
        return text.range(of: #"<depth[\s>/-]"#, options: .regularExpression) != nil
    }
}

final class ElmLabNoDepthTests: XCTestCase {
    private func parse(_ xml: String) throws -> Experiment {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".phyphox")
        try xml.write(to: url, atomically: true, encoding: .utf8)
        defer { try? FileManager.default.removeItem(at: url) }
        return try ExperimentSerialization.readExperimentFromURL(url)
    }

    func testDepthInputIsRefused() {
        XCTAssertThrowsError(try parse("""
        <phyphox version="1.15">
            <title>t</title><category>c</category>
            <data-containers><container size="100">z</container></data-containers>
            <input><depth mode="closest"><output component="z">z</output></depth></input>
        </phyphox>
        """))
    }

    func testDepthGUIIsRefused() {
        XCTAssertThrowsError(try parse("""
        <phyphox version="1.15">
            <title>t</title><category>c</category>
            <views><view label="v"><depth-gui label="Depth"/></view></views>
        </phyphox>
        """))
    }

    func testTheSameFileWithoutDepthLoads() throws {
        _ = try parse("""
        <phyphox version="1.15">
            <title>t</title><category>c</category>
            <data-containers><container size="100">z</container></data-containers>
            <input><sensor type="accelerometer"><output component="z">z</output></sensor></input>
            <views><view label="v"><info label="Hello"/></view></views>
        </phyphox>
        """)
    }

}
